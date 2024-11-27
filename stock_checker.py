import asyncio
import json
from pathlib import Path
from typing import Dict, Optional, List
import re
from datetime import datetime

from firecrawl import FirecrawlApp
from models import StockInfo, Product
from csv_handler import CSVHandler

class StockChecker:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.app = FirecrawlApp(api_key=api_key)
        self.csv_handler = CSVHandler()
        self.results_file = Path('stock_results.json')
        self.partial_results_file = Path('stock_results_partial.json')

    def _parse_stock_info(self, html: str) -> StockInfo:
        """Parse stock information from the HTML content"""
        stock_info = {}
        stores = ['Warehouse', 'Causeway Bay', 'Kowloon Bay', 'Macau Taipa', 'Shatin', 'Tsuen Wan']
        
        for store in stores:
            # First check for "Out of stock" message
            out_of_stock_pattern = f'Out of stock at\\s*{store}'
            if re.search(out_of_stock_pattern, html, re.IGNORECASE):
                stock_info[store] = 0
                continue

            # Then check for "In stock" message with quantity
            patterns = [
                f'In stock at\\s*{store}\\s*([0-9,]+)\\s*in stock',
                f'{store}[^0-9]*([0-9,]+)\\s*in stock',
                f'status__label[^>]*>[^>]*{store}[^0-9]*([0-9,]+)\\s*in stock'
            ]
            
            found = False
            for pattern in patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    try:
                        qty_str = match.group(1).replace(',', '')
                        stock_info[store] = int(qty_str)
                        found = True
                        break
                    except (ValueError, IndexError) as e:
                        print(f"Error parsing quantity for {store}: {e}")
            
            # If no stock information found, assume out of stock
            if not found:
                stock_info[store] = 0
        
        return StockInfo.from_dict(stock_info)

    async def _exponential_backoff(self, attempt: int, max_attempts: int = 5):
        """Implement exponential backoff for rate limiting"""
        if attempt >= max_attempts:
            raise Exception("Max retry attempts reached")
        wait_time = min(300, (2 ** attempt))
        print(f"Rate limited. Waiting {wait_time} seconds before retry...")
        await asyncio.sleep(wait_time)

    async def _scrape_product(self, url: str, attempt: int = 0) -> Optional[Dict]:
        """Scrape a single URL with retry logic"""
        print(f"\nChecking stock for: {url}")
        try:
            result = self.app.scrape_url(url, params={'formats': ['html']})
            if result and 'html' in result:
                return result
            print(f"Failed to scrape {url}")
            return None
        except Exception as e:
            if "429" in str(e) and attempt < 5:  # Rate limit error
                await self._exponential_backoff(attempt)
                return await self._scrape_product(url, attempt + 1)
            print(f"Error scraping {url}: {str(e)}")
            return None

    def _save_results(self, results: Dict, is_partial: bool = False):
        """Save results to file"""
        file_path = self.partial_results_file if is_partial else self.results_file
        results_with_timestamp = {
            'timestamp': datetime.now().isoformat(),
            'results': {url: stock_info.to_dict() for url, stock_info in results.items()}
        }
        with open(file_path, 'w') as f:
            json.dump(results_with_timestamp, f, indent=4)

    async def check_stock(self, batch_size: int = 2) -> Dict[str, StockInfo]:
        """Check stock for all products"""
        urls = self.csv_handler.get_all_product_urls()
        results = {}
        total_urls = len(urls)
        
        print(f"\nChecking stock for {total_urls} products")
        
        for i in range(0, total_urls, batch_size):
            batch = urls[i:i + batch_size]
            print(f"\nProgress: {i}/{total_urls} URLs processed ({(i/total_urls)*100:.1f}%)")
            
            tasks = []
            for url in batch:
                await asyncio.sleep(2)  # Rate limiting delay
                tasks.append(asyncio.create_task(self._scrape_product(url)))
            
            batch_results = await asyncio.gather(*tasks)
            
            for url, result in zip(batch, batch_results):
                if result and 'html' in result:
                    stock_info = self._parse_stock_info(result['html'])
                    results[url] = stock_info
                    product = self.csv_handler.get_product_by_url(url)
                    product_name = product.name if product else "Unknown Product"
                    print(f"\nStock information for {product_name} ({url}):")
                    print(stock_info)  # Will use the new string representation
                    
                    # Save partial results
                    self._save_results(results, is_partial=True)
            
            await asyncio.sleep(3)  # Batch delay
        
        self._save_results(results)
        return results

    def get_latest_stock_results(self) -> Optional[Dict]:
        """Get the latest stock results from file"""
        if self.results_file.exists():
            with open(self.results_file, 'r') as f:
                data = json.load(f)
                if 'results' in data:
                    return {url: StockInfo.from_dict(stock_data) 
                           for url, stock_data in data['results'].items()}
        return None
