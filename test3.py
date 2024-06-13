import asyncio
import aiofiles
import aiohttp
import json
from bs4 import BeautifulSoup
from aiohttp import ClientError

async def load_config(filename):
    """Loads the configuration file as a JSON object."""
    async with aiofiles.open(filename, 'r') as f:
        conf = json.loads(await f.read())
        return conf

async def fetch_url(session, url, retries=3):
    """Fetches a URL with retries."""
    for attempt in range(retries):
        try:
            async with session.get(url) as response:
                return await response.text()
        except ClientError as e:
            print(f"Attempt {attempt + 1} failed for {url}: {e}")
            await asyncio.sleep(2 ** attempt)  # Exponential backoff
    return None

async def get_product_urls(config, scraperapi_key):
    """Gets product URLs for each category using ScraperAPI."""
    product_urls = []

    async with aiohttp.ClientSession() as session:
        for category in config['product-category']:
            try:
                print(category['name'])
                if 'url' not in category:
                    print(f"Warning: 'url' key is missing in category: {category['name']}")
                    continue  # Skip this category if 'url' key is missing
                
                url = category['url']
                scraperapi_url = f"https://api.scraperapi.com?key={scraperapi_key}&url={url}"

                html_content = await fetch_url(session, scraperapi_url)
                if html_content is None:
                    print(f"Failed to fetch content for {url}")
                    continue

                soup = BeautifulSoup(html_content, 'lxml')

                product_links = soup.select(config['data_selectors']['product_url'])
                
                for link in product_links:
                    product_urls.append(link['href'])
            except Exception as e:
                print(f"Error processing category '{category['name']}': {e}")

    return product_urls

async def scrape_product_data(session, url, config, scraperapi_key):
    """Scrapes product data from a given URL using ScraperAPI."""
    data = {}
    scraperapi_url = f"https://api.scraperapi.com?key={scraperapi_key}&url={url}"

    html_content = await fetch_url(session, scraperapi_url)
    if html_content is None:
        print(f"Failed to fetch content for {url}")
        return None

    soup = BeautifulSoup(html_content, 'lxml')

    # Extract data for each option defined in config
    for option_name, selector in config['data_selectors']['options'].items():
        element = soup.select_one(selector)
        if element:
            data[option_name] = element.text.strip()

    # Extract SKU and stock level if they exist
    sku_element = soup.select_one(config['data_selectors']['sku'])
    if sku_element:
        data['sku'] = sku_element.text.strip()

    stock_level_element = soup.select_one(config['data_selectors']['stock_level'])
    if stock_level_element:
        data['stock_level'] = stock_level_element.text.strip()

    wholesale_price_element = soup.select_one(config['data_selectors']['wholesale_price'])
    if wholesale_price_element:
        data['wholesale_price'] = wholesale_price_element.text.strip()

    return data

async def main():
    config = await load_config('config.json')
    scraperapi_key = "9c8bd768187cf44d42e2b1ddfe117f6a"  # Replace with your ScraperAPI key

    product_urls = await get_product_urls(config, scraperapi_key)

    # Open the output file in append mode
    async with aiofiles.open("scraped_products.json", "a") as output_file:
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in product_urls:
                task = scrape_product_data(session, url, config, scraperapi_key)
                tasks.append(task)

            product_data_list = await asyncio.gather(*tasks)

            for product_data in product_data_list:
                # Only write non-null data to the output file
                if product_data:
                    json_data = json.dumps(product_data)
                    await output_file.write(json_data + "\n")

                    print(f"Product Name: {product_data.get('name')}")
                    print(f"SKU: {product_data.get('sku')}")
                    print(f"Stock Level: {product_data.get('stock_level')}")
                    print(f"Special Price: {product_data.get('special-price')}")
                    print("---")

    print("Scraped product data saved to scraped_products.json")

if __name__ == "__main__":
    asyncio.run(main())

