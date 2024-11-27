import csv
from typing import List, Dict, Optional
from pathlib import Path
from models import Product
from decimal import Decimal

class CSVHandler:
    def __init__(self, csv_path: str = 'ikea_products.csv'):
        self.csv_path = csv_path

    def _parse_price(self, price_str: str) -> Optional[Decimal]:
        """Parse price string to Decimal, handling various formats"""
        if not price_str:
            return None
        try:
            # Remove any currency symbols and commas
            cleaned = price_str.replace('$', '').replace(',', '').strip()
            if cleaned:
                return Decimal(cleaned)
            return None
        except (ValueError, TypeError, decimal.InvalidOperation):
            return None

    def _get_image_url(self, product_url: str) -> str:
        """Generate image URL from product URL"""
        # IKEA product URLs are like: .../product-name-art-12345678
        # Image URLs follow a pattern based on the article number
        try:
            article_number = product_url.split('-art-')[1]
            return f"https://www.ikea.com.hk/dairyfarm/hk/images/{article_number}.jpg"
        except IndexError:
            return ""

    def get_all_products(self) -> List[Product]:
        """Get all products from the CSV file"""
        products = []
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        price = self._parse_price(row.get('Price', ''))
                        image_url = self._get_image_url(row['Product URL'])
                        products.append(Product(
                            name=row.get('Product Name', ''),
                            url=row.get('Product URL', ''),
                            description=row.get('Description', ''),
                            image_url=image_url,
                            price=price
                        ))
                    except Exception as e:
                        print(f"Error parsing product: {row.get('Product Name', 'Unknown')}, Error: {e}")
                        continue
        except Exception as e:
            print(f"Error reading CSV file: {e}")
        return products

    def get_all_product_urls(self) -> List[str]:
        """Get all product URLs from the CSV file"""
        urls = []
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                urls = [row['Product URL'] for row in reader if row.get('Product URL')]
        except Exception as e:
            print(f"Error reading CSV file: {e}")
        return urls

    def get_product_by_url(self, url: str) -> Optional[Product]:
        """Get a specific product by its URL"""
        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('Product URL') == url:
                        price = self._parse_price(row.get('Price', ''))
                        image_url = self._get_image_url(url)
                        return Product(
                            name=row.get('Product Name', ''),
                            url=row.get('Product URL', ''),
                            description=row.get('Description', ''),
                            image_url=image_url,
                            price=price
                        )
        except Exception as e:
            print(f"Error reading CSV file: {e}")
        return None

    def update_product_image(self, url: str, new_image_url: str) -> bool:
        """Update the image URL for a specific product"""
        products = self.get_all_products()
        updated = False
        
        try:
            with open(self.csv_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['Product Name', 'Product URL', 'Description', 'Image', 'Price'])
                writer.writeheader()
                
                for product in products:
                    if product.url == url:
                        product.image_url = new_image_url
                        updated = True
                    
                    writer.writerow({
                        'Product Name': product.name,
                        'Product URL': product.url,
                        'Description': product.description,
                        'Image': product.image_url,
                        'Price': str(product.price) if product.price else ''
                    })
                
            return updated
        except Exception as e:
            print(f"Error updating CSV file: {e}")
            return False
