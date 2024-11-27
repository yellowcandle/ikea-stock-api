from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY')

# Database Configuration
DB_PATH = "ikea_products.db"

# File Paths
BASE_DIR = Path(__file__).parent
PRODUCT_IMAGES_DIR = BASE_DIR / "product_images"
STOCK_RESULTS_FILE = BASE_DIR / "stock_results.json"
PARTIAL_RESULTS_FILE = BASE_DIR / "stock_results_partial.json"

# Scraping Configuration
BATCH_SIZE = 2
MAX_RETRIES = 5
RATE_LIMIT_DELAY = 2  # seconds
BATCH_DELAY = 3  # seconds

# Store Names
STORES = [
    'Warehouse',
    'Causeway Bay',
    'Kowloon Bay',
    'Macau Taipa',
    'Shatin',
    'Tsuen Wan'
]
