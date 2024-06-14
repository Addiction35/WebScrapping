from bs4 import BeautifulSoup
import requests

def extract_product_data(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Example CSS selectors - Adjust these based on actual HTML structure
        if 'demandvape.com' in url:
            product_name = soup.select_one('div.product-name h1')
            product_price = soup.select_one('span.price')
        elif '1oakwholesale.com' in url:
            product_name = soup.select_one('h1.product-title')
            product_price = soup.select_one('span.product-price')
        else:
            return {'url': url, 'error': 'Unknown website'}

        # Extract and clean product name
        if product_name:
            product_name = product_name.get_text().strip()
        else:
            product_name = 'N/A'
        
        # Extract and clean product price
        if product_price:
            product_price = product_price.get_text().strip().replace('$', '')
        else:
            product_price = 'N/A'
        
        return {
            'url': url,
            'product_name': product_name,
            'product_price': product_price
        }
    except Exception as e:
        return {
            'url': url,
            'error': str(e)
        }

# Example URLs
urls = [
    "https://demandvape.com/liquids/reds-apple-7obacco-100ml",
    "https://1oakwholesale.com/geekvape-peak-kit.html",
    "https://demandvape.com/liquids/prohibition-juice-co-blind-pig-100ml",
    "https://1oakwholesale.com/exxus-vape-snap-vv-pro.html"
]

for url in urls:
    data = extract_product_data(url)
    print(data)

