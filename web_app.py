from flask import Flask, render_template, jsonify
import pandas as pd
from stock_checker import StockChecker
from config import FIRECRAWL_API_KEY
import os
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta

app = Flask(__name__)

# Configure static folder for product images
app.static_folder = 'static'
os.makedirs(app.static_folder, exist_ok=True)

# Create symbolic link to product_images in static folder
product_images_link = Path(app.static_folder) / 'product_images'
if not product_images_link.exists():
    os.symlink(Path('product_images').absolute(), product_images_link)

# Cache for stock data
stock_cache = {
    'data': None,
    'timestamp': None
}

def format_price(price):
    """Format price value"""
    if pd.isna(price):
        return "N/A"
    try:
        # Handle string prices that might start with +
        price_str = str(price).replace('+', '').strip()
        price_float = float(price_str.replace(',', ''))
        return f"HK${price_float:,.1f}"
    except (ValueError, TypeError, AttributeError):
        return "N/A"

def get_stock_data():
    """Get stock data with caching"""
    current_time = datetime.now()
    
    # If cache exists and is less than 4 hours old, return cached data
    if stock_cache['data'] is not None and stock_cache['timestamp'] is not None:
        age = current_time - stock_cache['timestamp']
        if age < timedelta(hours=4):
            return stock_cache['data']
    
    # Otherwise, fetch new data
    stock_checker = StockChecker(FIRECRAWL_API_KEY)
    stock_data = stock_checker.get_latest_stock_results() or {}
    
    # Update cache
    stock_cache['data'] = stock_data
    stock_cache['timestamp'] = current_time
    
    return stock_data

def get_product_data():
    """Get combined product and stock data"""
    # Read product data from both CSV files
    df_prices = pd.read_csv('ikea_products.csv')
    df_images = pd.read_csv('ikea_products_with_images.csv')
    
    # Clean column names
    df_prices.columns = df_prices.columns.str.strip()
    df_images.columns = df_images.columns.str.strip()
    
    # Drop any existing price column from images DataFrame
    if 'Price' in df_images.columns:
        df_images = df_images.drop('Price', axis=1)
    
    # Create a base DataFrame with unique product URLs
    df = df_images.drop_duplicates(subset=['Product URL'], keep='first')
    
    # Clean up Product URL in both dataframes
    df['Product URL'] = df['Product URL'].str.strip()
    df_prices['Product URL'] = df_prices['Product URL'].str.strip()
    
    # Merge with price data
    df = pd.merge(
        df,
        df_prices[['Product URL', 'Price']],
        on='Product URL',
        how='left'
    )
    
    # Get stock information from cache or update if needed
    stock_data = get_stock_data()
    
    # Process data for display
    products = []
    seen_urls = set()
    
    for _, row in df.iterrows():
        # Skip duplicates
        if row['Product URL'] in seen_urls:
            continue
        seen_urls.add(row['Product URL'])
        
        # Get stock info for this product
        stock_info = stock_data.get(row['Product URL'], None)
        stock_status = stock_info.to_dict() if stock_info else {}
        
        # Create product entry
        product = {
            'name': row['Product Name'],
            'url': row['Product URL'],
            'description': row['Description'] if pd.notna(row['Description']) else 'N/A',
            'price': format_price(row['Price']),
            'image_path': f"/static/product_images/{os.path.basename(row['Local Image Path'])}" if pd.notna(row['Local Image Path']) else None,
            'stock': {
                'Warehouse': stock_status.get('Warehouse', 0),
                'Causeway Bay': stock_status.get('Causeway Bay', 0),
                'Kowloon Bay': stock_status.get('Kowloon Bay', 0),
                'Macau Taipa': stock_status.get('Macau Taipa', 0),
                'Shatin': stock_status.get('Shatin', 0),
                'Tsuen Wan': stock_status.get('Tsuen Wan', 0)
            }
        }
        products.append(product)
    
    # Sort products by name
    products.sort(key=lambda x: x['name'])
    return products

@app.route('/')
def index():
    products = get_product_data()
    last_update = stock_cache['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if stock_cache['timestamp'] else 'Never'
    next_update = (stock_cache['timestamp'] + timedelta(hours=4)).strftime('%Y-%m-%d %H:%M:%S') if stock_cache['timestamp'] else 'Unknown'
    return render_template('index.html', products=products, datetime=datetime, last_update=last_update, next_update=next_update)


if __name__ == '__main__':
    app.run(debug=True)
