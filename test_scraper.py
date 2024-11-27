import asyncio
from image_scraper import ImageScraper
import pandas as pd

async def main():
    # Initialize the scraper
    scraper = ImageScraper(image_dir='product_images')
    
    # Read the CSV file
    df = pd.read_csv('ikea_products.csv')
    
    # Take first 3 product URLs for testing
    test_urls = df['Product URL'].dropna().head(3).tolist()
    
    print("Starting image scraping test...")
    print(f"Testing with URLs: {test_urls}")
    
    # Test the scraper
    results = await scraper.scrape_all_images(test_urls)
    
    print("\nScraping completed!")
    print(f"Downloaded {len(results)} images")
    for url, path in results.items():
        print(f"URL: {url}\nSaved to: {path}\n")

if __name__ == "__main__":
    asyncio.run(main())
