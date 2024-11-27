import asyncio
import aiohttp
from bs4 import BeautifulSoup
import csv
from pathlib import Path
from image_scraper import ImageScraper
from typing import List, Dict, Optional, Tuple
import logging
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class Product:
    name: str
    url: str
    description: str
    price: str
    image_url: Optional[str] = None
    local_image_path: Optional[str] = None

class IkeaImageDownloader:
    def __init__(self):
        self.scraper = ImageScraper()
        self.session: Optional[aiohttp.ClientSession] = None
        self.products: List[Product] = []

    async def get_product_image_url(self, product_url: str) -> Optional[str]:
        """Extract the main product image URL from the product page"""
        if not self.session:
            return None
        
        try:
            async with self.session.get(product_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch {product_url}: Status {response.status}")
                    return None
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # Look for the product image
                img = soup.select_one('.mx-auto.d-block.keen-slider-detail-image')
                if img and 'src' in img.attrs:
                    return img['src']
                
                logger.warning(f"No image found for {product_url}")
                return None
        except Exception as e:
            logger.error(f"Error fetching {product_url}: {str(e)}")
            return None

    async def process_product(self, product: Product):
        """Process a single product and update its image information"""
        image_url = await self.get_product_image_url(product.url)
        if image_url:
            product.image_url = image_url
            image_path = await self.scraper.download_direct_image(image_url)
            if image_path:
                product.local_image_path = image_path
                logger.info(f"Successfully downloaded image for {product.name} -> {image_path}")
            else:
                logger.error(f"Failed to download image for {product.name}")
        else:
            logger.error(f"No image URL found for {product.name}")

    async def process_batch(self, batch_size: int = 5):
        """Process a batch of products concurrently"""
        for i in range(0, len(self.products), batch_size):
            batch = self.products[i:i + batch_size]
            tasks = [self.process_product(product) for product in batch]
            await asyncio.gather(*tasks)
            
            # Add a small delay between batches to be nice to the server
            await asyncio.sleep(1)

    def read_products(self, csv_path: str):
        """Read products from CSV file"""
        self.products = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'Product URL' in row and row['Product URL']:
                    product = Product(
                        name=row.get('Product Name', ''),
                        url=row['Product URL'],
                        description=row.get('Description', ''),
                        price=row.get('Price', '')
                    )
                    self.products.append(product)
        logger.info(f"Found {len(self.products)} products to process")

    def save_product_mapping(self, output_path: str = 'ikea_products_with_images.csv'):
        """Save products with their image mappings to CSV"""
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['Product Name', 'Product URL', 'Description', 'Price', 'Image URL', 'Local Image Path'])
            # Write product data
            for product in self.products:
                writer.writerow([
                    product.name,
                    product.url,
                    product.description,
                    product.price,
                    product.image_url or '',
                    product.local_image_path or ''
                ])
        logger.info(f"Saved product-image mapping to {output_path}")

    async def download_all_images(self, csv_path: str = 'ikea_products.csv'):
        """Main method to download all product images"""
        self.read_products(csv_path)
        
        # Create aiohttp session
        async with aiohttp.ClientSession() as session:
            self.session = session
            await self.process_batch()
        
        self.session = None
        
        # Save the mapping
        self.save_product_mapping()

async def main():
    downloader = IkeaImageDownloader()
    await downloader.download_all_images()

if __name__ == "__main__":
    asyncio.run(main())
