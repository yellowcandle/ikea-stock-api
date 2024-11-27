import aiohttp
import asyncio
from pathlib import Path
from typing import Optional, Dict, List
import hashlib
import base64
from urllib.parse import urlparse
import os
from firecrawl import FirecrawlApp
from csv_handler import CSVHandler
from config import FIRECRAWL_API_KEY

class ImageScraper:
    def __init__(self, image_dir: str = 'product_images'):
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(exist_ok=True)
        self.csv_handler = CSVHandler()
        self.downloaded_images: Dict[str, str] = {}
        self.app = FirecrawlApp(api_key=FIRECRAWL_API_KEY)

    def _get_image_filename(self, url: str) -> str:
        """Generate a unique filename for an image URL while preserving extension"""
        # Parse the URL to get the path
        parsed_url = urlparse(url)
        # Get the original file extension
        _, ext = os.path.splitext(parsed_url.path)
        if not ext:
            ext = '.png'  # Default to .png if no extension found
        # Create a hash of the URL to use as filename
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return f"{url_hash}{ext}"

    async def _download_image_direct(self, image_url: str) -> Optional[Path]:
        """Download image directly from URL"""
        if not image_url:
            return None

        filename = self._get_image_filename(image_url)
        file_path = self.image_dir / filename

        # Skip if already downloaded
        if file_path.exists():
            self.downloaded_images[image_url] = str(file_path)
            return file_path

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status == 200:
                        content = await response.read()
                        file_path.write_bytes(content)
                        self.downloaded_images[image_url] = str(file_path)
                        print(f"Downloaded image: {image_url} -> {file_path}")
                        return file_path
                    else:
                        print(f"Failed to download image {image_url}: Status {response.status}")
                        return None
        except Exception as e:
            print(f"Error downloading image {image_url}: {str(e)}")
            return None

    async def _download_image(self, product_url: str) -> Optional[Path]:
        """Download product image using screenshot"""
        if not product_url:
            return None

        filename = self._get_image_filename(product_url)
        file_path = self.image_dir / filename

        # Skip if already downloaded
        if file_path.exists():
            self.downloaded_images[product_url] = str(file_path)
            return file_path

        try:
            # Use FireCrawl to get a screenshot of the product page
            result = self.app.scrape_url(product_url, params={
                'formats': ['screenshot'],
                'screenshotOptions': {
                    'selector': '.product-image img',  # Target the product image
                    'fullPage': False
                }
            })
            
            if result and 'screenshot' in result:
                # Decode base64 screenshot data
                image_data = base64.b64decode(result['screenshot'])
                file_path.write_bytes(image_data)
                self.downloaded_images[product_url] = str(file_path)
                print(f"Downloaded image for product: {product_url} -> {file_path}")
                return file_path
            else:
                print(f"Failed to capture image for product {product_url}: No screenshot data received")
                return None
        except Exception as e:
            print(f"Error capturing image for product {product_url}: {str(e)}")
            return None

    async def _download_batch(self, urls: List[str], batch_size: int = 2, direct_image: bool = False):
        """Download a batch of images"""
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            if direct_image:
                tasks = [self._download_image_direct(url) for url in batch]
            else:
                tasks = [self._download_image(url) for url in batch]
            await asyncio.gather(*tasks)
            # Add a delay between batches to respect rate limits
            await asyncio.sleep(1)

    async def download_direct_image(self, image_url: str) -> Optional[str]:
        """Download a single image directly from its URL"""
        result = await self._download_image_direct(image_url)
        return str(result) if result else None

    async def scrape_all_images(self, urls: List[str], direct_image: bool = False) -> Dict[str, str]:
        """Download all product images"""
        print(f"Starting download of {len(urls)} images...")
        
        # Clear the downloaded images dictionary
        self.downloaded_images.clear()
        
        # Download images in batches
        await self._download_batch(urls, direct_image=direct_image)
        
        print(f"Downloaded {len(self.downloaded_images)} images successfully")
        return self.downloaded_images

    def get_image_path(self, url: str) -> Optional[str]:
        """Get the local path for a downloaded image"""
        if url in self.downloaded_images:
            return self.downloaded_images[url]
        
        # Check if image exists on disk
        filename = self._get_image_filename(url)
        file_path = self.image_dir / filename
        if file_path.exists():
            self.downloaded_images[url] = str(file_path)
            return str(file_path)
        
        return None

    def get_all_downloaded_images(self) -> Dict[str, str]:
        """Get a dictionary of all downloaded images (url -> local path)"""
        return self.downloaded_images.copy()
