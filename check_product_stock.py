import pandas as pd
from firecrawl import FirecrawlApp
import duckdb
from pprint import pprint
import time
from pathlib import Path
import shutil
import tempfile
import json
import asyncio
from typing import List, Dict
import aiohttp
import re
from config import FIRECRAWL_API_KEY

api_key = FIRECRAWL_API_KEY

def parse_stock_info(result: dict) -> dict:
    """Parse stock information from the scraping result"""
    stock_info = {}
    
    # Extract stock information using the HTML content
    if 'html' in result:
        html = result['html']
        
        # Debug: Print a section of HTML containing stock info
        if 'status status--green' in html:
            start_idx = html.find('status status--green')
            print("\nDebug - HTML section with stock info:")
            print(html[start_idx:start_idx + 500])
        
        # Look for stock status divs with the specific format
        stores = ['Warehouse', 'Causeway Bay', 'Kowloon Bay', 'Macau Taipa', 'Shatin', 'Tsuen Wan']
        for store in stores:
            # Pattern to match stock information in different formats
            patterns = [
                f'In stock at\\s*{store}\\s*([0-9,]+)\\s*in stock',  # Format: "In stock at Store X in stock"
                f'{store}[^0-9]*([0-9,]+)\\s*in stock',  # Format: "Store X in stock"
                f'status__label[^>]*>[^>]*{store}[^0-9]*([0-9,]+)\\s*in stock'  # Format in status label
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    try:
                        qty_str = match.group(1).replace(',', '')  # Remove commas from numbers
                        qty = int(qty_str)
                        stock_info[store] = qty
                        break  # Found a match, no need to try other patterns
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing quantity for {store}: {e}")
            
            if store not in stock_info:
                stock_info[store] = 0
    
    return stock_info

async def exponential_backoff(attempt: int, max_attempts: int = 5):
    """Implement exponential backoff for rate limiting"""
    if attempt >= max_attempts:
        raise Exception("Max retry attempts reached")
    wait_time = min(300, (2 ** attempt))  # Cap at 300 seconds
    print(f"Rate limited. Waiting {wait_time} seconds before retry...")
    await asyncio.sleep(wait_time)

def get_product_urls(max_retries=3, delay=1) -> List[str]:
    db_path = Path('ikea_products.db')
    
    if not db_path.exists():
        print(f"Database file {db_path} not found")
        return []

    # Create a temporary copy of the database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        try:
            # Copy the database to a temporary file
            shutil.copy2(db_path, temp_db.name)
            
            # Connect to the temporary database copy
            with duckdb.connect(temp_db.name, read_only=True) as conn:
                try:
                    result = conn.execute("SELECT DISTINCT product_url FROM ikea_products").fetchall()
                    urls = [row[0] for row in result]
                    return urls
                except duckdb.Error as e:
                    print(f"Error querying database: {e}")
                    return []
                
        except (IOError, duckdb.Error) as e:
            print(f"Error accessing database: {e}")
            return []
        finally:
            # Clean up temporary file
            try:
                Path(temp_db.name).unlink()
            except:
                pass

async def scrape_product(app: FirecrawlApp, url: str, attempt: int = 0) -> Dict:
    """Scrape a single URL with retry logic"""
    print(f"\nScraping: {url}")
    try:
        # Scrape URL and get result directly
        result = app.scrape_url(url, params={'formats': ['markdown', 'html']})
        if result:
            return result
        else:
            print(f"Failed to scrape {url}")
            return None
    except Exception as e:
        if "429" in str(e) and attempt < 5:  # Rate limit error
            await exponential_backoff(attempt)
            return await scrape_product(app, url, attempt + 1)
        print(f"Error scraping {url}: {str(e)}")
        return None

async def process_urls(urls: List[str], batch_size: int = 2) -> Dict:
    """Process URLs in batches with smaller batch size and longer delay"""
    results = {}
    app = FirecrawlApp(api_key=api_key)
    total_urls = len(urls)
    
    # Process URLs in batches
    for i in range(0, total_urls, batch_size):
        batch = urls[i:i + batch_size]
        print(f"\nProgress: {i}/{total_urls} URLs processed ({(i/total_urls)*100:.1f}%)")
        
        # Create tasks for concurrent processing
        tasks = []
        for url in batch:
            # Add longer delay between requests
            await asyncio.sleep(2)
            tasks.append(asyncio.create_task(scrape_product(app, url)))
        
        # Wait for all tasks in batch to complete
        batch_results = await asyncio.gather(*tasks)
        
        # Process results
        for url, result in zip(batch, batch_results):
            if result:
                stock_info = parse_stock_info(result)
                if stock_info:  # Only store if we found stock information
                    results[url] = stock_info
                    print(f"\nStock information for {url}:")
                    pprint(stock_info)
                    
                    # Save results after each successful scrape
                    with open('stock_results_partial.json', 'w') as f:
                        json.dump(results, f, indent=4)
        
        # Add delay between batches
        await asyncio.sleep(3)
    
    return results

async def main():
    # Get URLs from database
    urls = get_product_urls()
    print(f"\nFound {len(urls)} unique URLs in database")
    
    if not urls:
        print("No URLs found in database")
        return
    
    try:
        # Process URLs and get results
        results = await process_urls(urls)
        
        # Save final results
        with open('stock_results.json', 'w') as f:
            json.dump(results, f, indent=4)
        print("\nResults saved to stock_results.json")
        
    except KeyboardInterrupt:
        print("\nScript interrupted by user. Saving partial results...")
        # Final results should already be saved in stock_results_partial.json
        print("Partial results saved in stock_results_partial.json")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nScript terminated by user")
