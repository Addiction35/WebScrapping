import asyncio
import aiofiles
import aiohttp
import requests
import json
from bs4 import BeautifulSoup

async def load_config(filename):
    """Loads the configuration file as a JSON object."""
    async with aiofiles.open(filename, 'r') as f:
        conf = json.loads(await f.read())
        return conf

async def get_product_urls(config, scraperapi_key):
    """Gets product URLs for each category using ScraperAPI."""
    product_urls = []

    for category in config['product-category']:
        print(category['name'])

        url = category['selector'].split("'")[1]
        scraperapi_url = f"https://api.scraperapi.com?key={scraperapi_key}&url={url}"

        async with aiohttp.ClientSession() as session:
            async with session.get(scraperapi_url) as response:
                html_content = await response.text()
                soup = BeautifulSoup(html_content, 'lxml')

                product_links = soup.find_all('a', class_="product-item-link")

                for link in product_links:
                    product_urls.append(link.get('href'))

    return product_urls

async def scrape_product_data(session, url, config, scraperapi_key):
    """Scrapes product data from a given URL using ScraperAPI."""
    data = {}
    scraperapi_url = f"https://api.scraperapi.com?key={scraperapi_key}&url={url}"

    async with session.get(scraperapi_url) as response:
        html_content = await response.text()
        soup = BeautifulSoup(html_content, 'lxml')

        for option_name, selector in config['data_selectors']['options'].items():
            data[option_name] = soup.select_one(selector).text.strip() if soup.select_one(selector) else None

        data['sku'] = soup.select_one(config['data_selectors']['sku']).text.strip() if soup.select_one(
            config['data_selectors']['sku']) else None
        data['stock_level'] = soup.select_one(config['data_selectors']['stock_level']).text.strip() if soup.select_one(
            config['data_selectors']['stock_level']) else None

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

