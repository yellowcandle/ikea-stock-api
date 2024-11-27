from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

def scrape_ikea_products_selenium():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36')
    
    # Initialize the driver
    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    try:
        # Navigate to the page
        url = "https://www.ikea.com.hk/en/search?q=plate&page=2&pa%5B%5D=50287"
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Add a small delay to let the page load
        time.sleep(5)
        
        # Wait for products to load - using selectors from the HTML fragment
        print("Waiting for products to load...")
        products_element = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "productList"))
        )
        
        # Get all products
        products = []
        print("Finding product elements...")
        product_elements = driver.find_elements(By.CLASS_NAME, "itemBlock")
        
        print(f"Found {len(product_elements)} product elements")
        
        for element in product_elements:
            try:
                name_element = element.find_element(By.CLASS_NAME, "itemName")
                name = name_element.find_element(By.TAG_NAME, "h6").text
                price_element = element.find_element(By.CLASS_NAME, "itemNormalPrice")
                price = price_element.text.strip().replace('$', '')
                img_element = element.find_element(By.CLASS_NAME, "productImg")
                image_url = img_element.find_element(By.TAG_NAME, "img").get_attribute("src")
                product_url = element.find_element(By.CSS_SELECTOR, "a.product-link").get_attribute("href")
                
                product_data = {
                    'name': name,
                    'price': price,
                    'image_url': image_url,
                    'product_url': product_url
                }
                products.append(product_data)
                print(f"Scraped product: {name}")
                
            except Exception as e:
                print(f"Error scraping product: {str(e)}")
                continue
            
        # Save to JSON file
        with open('ikea_products.json', 'w', encoding='utf-8') as f:
            json.dump(products, f, ensure_ascii=False, indent=2)
            
        return products
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []
        
    finally:
        driver.quit()

if __name__ == "__main__":
    products = scrape_ikea_products_selenium()
    if products:
        print(f"Successfully scraped {len(products)} products")
    else:
        print("No products were scraped")
