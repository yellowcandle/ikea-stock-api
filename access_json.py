import re
import orjson
import duckdb
from pprint import pprint

# Read and parse the JSON files
files = ['ikea_products_1.json', 'ikea_products_2.json']
all_products = []

def clean_price(price_str):
    if not price_str:
        return None
    # Remove $ and convert to float
    try:
        return float(price_str.replace('$', ''))
    except ValueError:
        return None

for file in files:
    with open(file, 'rb') as f:
        products = orjson.loads(f.read())
        markdown_content = products['data'][0]['markdown']

    # Extract product details using regex
    url_pattern = r'\[(?:\*\*)?([^\]]+?)(?:\*\*)?\]\((https://www\.ikea\.com\.hk/en/products/dining-and-serving/dinnerware-and-serving/[^/]+?-art-\d+)\)'
    desc_pattern = r'\]\(https://.*?\)\n\n(.*?)\n\n\$'
    image_pattern = r'\!\[.*?\]\((.*?)\)'
    price_pattern = r'\$(\d+\.?\d*)'

    product_entries = set(re.findall(url_pattern, markdown_content))
    descriptions = re.findall(desc_pattern, markdown_content)
    images = re.findall(image_pattern, markdown_content)
    prices = re.findall(price_pattern, markdown_content)

    for i, (product_name, product_url) in enumerate(sorted(product_entries)):
        description = descriptions[i] if i < len(descriptions) else ""
        image = images[i] if i < len(images) else ""
        price = prices[i] if i < len(prices) else ""
        price_float = clean_price(price)  # Convert price to float or None
        all_products.append((product_name, product_url, description, image, price_float))

# Save to CSV file
import csv

csv_file = 'ikea_products.csv'

with open(csv_file, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['Product Name', 'Product URL', 'Description', 'Image URL', 'Price'])
    writer.writerows(all_products)

print(f"Product details saved to {csv_file}")

# Verify data
with open(csv_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    next(reader)  # Skip header
    for row in reader:
        pprint(row)
