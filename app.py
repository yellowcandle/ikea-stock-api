import asyncio
import argparse
from typing import Optional, Dict, List
import json
from pathlib import Path
from collections import defaultdict

from config import FIRECRAWL_API_KEY
from stock_checker import StockChecker
from image_scraper import ImageScraper
from csv_handler import CSVHandler
from models import StockInfo

def print_stock_summary(results: Dict[str, StockInfo], csv_handler: CSVHandler):
    """Print a summary of stock information"""
    store_totals = defaultdict(int)
    out_of_stock_products = []
    well_stocked_products = []
    
    for url, stock in results.items():
        product = csv_handler.get_product_by_url(url)
        product_name = product.name if product else "Unknown Product"
        
        # Update store totals
        for store, qty in stock.to_dict().items():
            store_totals[store] += qty
        
        # Check if product is out of stock everywhere
        if all(qty == 0 for qty in stock.to_dict().values()):
            out_of_stock_products.append(product_name)
        # Check if product is well stocked (more than 50 total items)
        elif sum(stock.to_dict().values()) > 50:
            well_stocked_products.append((product_name, sum(stock.to_dict().values())))
    
    print("\nStock Summary")
    print("=" * 80)
    
    print("\nStore Totals:")
    for store, total in sorted(store_totals.items(), key=lambda x: x[1], reverse=True):
        print(f"{store}: {total} items")
    
    print("\nOut of Stock Products:")
    if out_of_stock_products:
        for product in sorted(out_of_stock_products):
            print(f"- {product}")
    else:
        print("No products completely out of stock")
    
    print("\nWell Stocked Products (>50 items):")
    if well_stocked_products:
        for product, total in sorted(well_stocked_products, key=lambda x: x[1], reverse=True):
            print(f"- {product}: {total} items")
    else:
        print("No products with more than 50 items in stock")

async def check_stock(output_file: Optional[str] = None):
    """Check stock for all products"""
    checker = StockChecker(FIRECRAWL_API_KEY)
    csv_handler = CSVHandler()
    results = await checker.check_stock()
    
    if output_file:
        with open(output_file, 'w') as f:
            json.dump({
                'results': {url: stock.to_dict() for url, stock in results.items()}
            }, f, indent=4)
        print(f"\nStock results saved to {output_file}")
    
    print_stock_summary(results, csv_handler)
    return results

async def download_images():
    """Download all product images"""
    scraper = ImageScraper()
    results = await scraper.scrape_all_images()
    print(f"\nDownloaded {len(results)} images")
    return results

def list_products():
    """List all products from CSV"""
    csv_handler = CSVHandler()
    products = csv_handler.get_all_products()
    
    print("\nProduct List:")
    print("-" * 80)
    for product in products:
        print(f"Name: {product.name}")
        print(f"URL: {product.url}")
        print(f"Description: {product.description}")
        print(f"Price: {'$' + str(product.price) if product.price else 'N/A'}")
        print("-" * 80)
    
    return products

async def main():
    parser = argparse.ArgumentParser(description='IKEA Product Stock Checker')
    parser.add_argument('action', choices=['check-stock', 'download-images', 'list-products'],
                      help='Action to perform')
    parser.add_argument('--output', '-o', help='Output file for stock results')
    
    args = parser.parse_args()
    
    try:
        if args.action == 'check-stock':
            await check_stock(args.output)
        elif args.action == 'download-images':
            await download_images()
        elif args.action == 'list-products':
            list_products()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
