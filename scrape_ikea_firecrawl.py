from firecrawl import FirecrawlApp
import orjson
import os
from config import FIRECRAWL_API_KEY

def crawl_ikea_website(url, api_key):
    app = FirecrawlApp(api_key=api_key)
    return app.crawl_url(
        url,
        params={
            'limit': 100,
            'scrapeOptions': {'formats': ['markdown', 'html']}
        },
        poll_interval=30
    )

def write_to_file(data, filename):
    with open(filename, 'wb') as f:
        f.write(orjson.dumps(data))

def read_from_file(filename):
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return orjson.loads(f.read())
    return None

def extract_markdown(data):
    if data and 'data' in data and data['data']:
        return data['data'][0].get('markdown')
    return None

def main():
    api_key = FIRECRAWL_API_KEY
    urls = ['https://www.ikea.com.hk/en/search?q=plate&pa%5B%5D=50287', 'https://www.ikea.com.hk/en/search?q=plate&page=2&pa%5B%5D=50287']
    
    for i, url in enumerate(urls):
        filename = f'ikea_products_{i+1}.json'
        crawl_status = crawl_ikea_website(url, api_key)
        write_to_file(crawl_status, filename)
        
        data = read_from_file(filename)
        markdown_content = extract_markdown(data)
        
        if markdown_content:
            print(f"Markdown content for {url}:")
            print(markdown_content)
        else:
            print(f"No markdown content found for {url}.")

if __name__ == "__main__":
    main()
