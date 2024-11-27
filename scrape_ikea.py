import requests
from bs4 import BeautifulSoup
import json
from time import sleep

def scrape_ikea_products():
    # Base URL
    url = "https://www.ikea.com.hk/en/search"
    
    # Parameters for the search
    params = {
        'q': 'plate',
        'page': 2,
        'pa[]': '50287'
    }
    
    # Headers to mimic a browser request
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        # Make the request
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Initialize list to store products
        products = []
        
        # Find the specific product container using the given XPath-like selector
        product_element = soup.select_one('#card_10258914 > div:nth-of-type(1) > a')
        
        if product_element:
            product_data = {
                'name': product_element.find('span', class_='product-compact__name').text.strip() if product_element.find('span', class_='product-compact__name') else None,
                'price': product_element.find('span', class_='product-compact__price').text.strip() if product_element.find('span', class_='product-compact__price') else None,
                'image_url': product_element.find('img')['src'] if product_element.find('img') else None,
                'product_url': product_element['href'] if product_element else None
            }
            products.append(product_data)
        
        # Save to JSON file
        with open('ikea_products.json', 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
            
        return products
        
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

if __name__ == "__main__":
    products = scrape_ikea_products()
    if products:
        print(f"Successfully scraped {len(products)} products") 