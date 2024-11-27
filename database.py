import duckdb
import time
import shutil
from pathlib import Path
from typing import List, Optional
from models import Product
from decimal import Decimal
import tempfile
import atexit
import os

class Database:
    def __init__(self, db_path: str = 'ikea_products.db'):
        self.original_db_path = db_path
        self.working_db_path = self._create_working_copy(db_path)
        self._ensure_db_exists()
        # Register cleanup on program exit
        atexit.register(self._cleanup)

    def _create_working_copy(self, original_path: str) -> str:
        """Create a working copy of the database in a temporary directory"""
        temp_dir = tempfile.mkdtemp()
        working_path = os.path.join(temp_dir, 'working_ikea_products.db')
        
        if os.path.exists(original_path):
            try:
                shutil.copy2(original_path, working_path)
            except Exception as e:
                print(f"Warning: Could not copy original database: {e}")
        
        return working_path

    def _cleanup(self):
        """Clean up temporary files"""
        try:
            if os.path.exists(self.working_db_path):
                os.remove(self.working_db_path)
            temp_dir = os.path.dirname(self.working_db_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temporary files: {e}")

    def _connect_with_retry(self, read_only: bool = False, max_retries: int = 3) -> duckdb.DuckDBPyConnection:
        """Connect to database with retry logic"""
        for attempt in range(max_retries):
            try:
                conn = duckdb.connect(self.working_db_path, read_only=read_only)
                return conn
            except duckdb.IOException as e:
                if attempt < max_retries - 1:
                    print(f"Database connection failed, retrying in {2 ** attempt} seconds...")
                    time.sleep(2 ** attempt)
                else:
                    raise

    def _ensure_db_exists(self):
        """Ensure database exists and has correct schema"""
        try:
            with self._connect_with_retry() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS ikea_products (
                        product_name VARCHAR,
                        product_url VARCHAR,
                        description VARCHAR,
                        image_url VARCHAR,
                        price DECIMAL(10, 2) NULL
                    )
                """)
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise

    def get_all_product_urls(self) -> List[str]:
        """Get all product URLs from the database"""
        try:
            with self._connect_with_retry(read_only=True) as conn:
                result = conn.execute("SELECT DISTINCT product_url FROM ikea_products").fetchall()
                return [row[0] for row in result]
        except Exception as e:
            print(f"Error getting product URLs: {e}")
            return []

    def get_all_products(self) -> List[Product]:
        """Get all products from the database"""
        try:
            with self._connect_with_retry(read_only=True) as conn:
                result = conn.execute("""
                    SELECT product_name, product_url, description, image_url, price 
                    FROM ikea_products
                """).fetchall()
                
                return [
                    Product(
                        name=row[0],
                        url=row[1],
                        description=row[2],
                        image_url=row[3],
                        price=Decimal(str(row[4])) if row[4] is not None else None
                    )
                    for row in result
                ]
        except Exception as e:
            print(f"Error getting products: {e}")
            return []

    def get_product_by_url(self, url: str) -> Optional[Product]:
        """Get a specific product by its URL"""
        try:
            with self._connect_with_retry(read_only=True) as conn:
                result = conn.execute("""
                    SELECT product_name, product_url, description, image_url, price 
                    FROM ikea_products 
                    WHERE product_url = ?
                """, [url]).fetchone()
                
                if result:
                    return Product(
                        name=result[0],
                        url=result[1],
                        description=result[2],
                        image_url=result[3],
                        price=Decimal(str(result[4])) if result[4] is not None else None
                    )
                return None
        except Exception as e:
            print(f"Error getting product by URL: {e}")
            return None

    def update_product_image(self, url: str, new_image_url: str) -> bool:
        """Update the image URL for a specific product"""
        try:
            with self._connect_with_retry() as conn:
                conn.execute("""
                    UPDATE ikea_products 
                    SET image_url = ? 
                    WHERE product_url = ?
                """, [new_image_url, url])
                return True
        except Exception as e:
            print(f"Error updating product image: {e}")
            return False

    def save_changes(self):
        """Save changes back to the original database file"""
        try:
            shutil.copy2(self.working_db_path, self.original_db_path)
            return True
        except Exception as e:
            print(f"Error saving changes to original database: {e}")
            return False
