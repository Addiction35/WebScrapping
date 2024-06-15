import asyncio
import aiofiles
import json
import logging
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp
import requests
import time

logging.basicConfig(level=logging.INFO)  # Set logging level to INFO

async def load_config(filename):
    """Loads the configuration file as a JSON object."""
    async with aiofiles.open(filename, 'r') as f:
        conf = json.loads(await f.read())
        return conf

async def get_product_urls(config, firecrawl_app):
    """Gets product URLs for each category using FireCrawl."""
    product_urls = []

    for site_config in config:
        logging.info(f"Processing site: {site_config['url']}")

        if 'product-category' not in site_config or not isinstance(site_config['product-category'], list):
            logging.error(f"'product-category' missing or not a list in the configuration for site: {site_config['url']}")
            continue

        for category in site_config['product-category']:
            logging.info(f"Category: {category['name']}")

            url = category['selector'].split("'")[1]
            retries = 3  # Number of retries
            backoff_time = 1  # Initial backoff time in seconds

            while retries > 0:
                try:
                    response = firecrawl_app.scrape_url(url=url)
                    response.raise_for_status()

                    # Check if the response can be parsed as JSON
                    try:
                        response_json = response.json()
                        html_content = response_json.get('content')
                        if not html_content:
                            logging.warning(f"No content found for URL: {url}")
                            continue

                        soup = BeautifulSoup(html_content, 'lxml')
                        product_links = soup.find_all('a', class_="product-item-link")

                        for link in product_links:
                            product_urls.append(link.get('href'))

                        break  # Exit the retry loop if successful

                    except json.JSONDecodeError as json_err:
                        logging.error(f"JSON decoding error for URL {url}: {json_err}")
                        retries -= 1
                        if retries > 0:
                            logging.info(f"Retrying in {backoff_time} seconds...")
                            await asyncio.sleep(backoff_time)
                            backoff_time *= 2  # Exponential backoff

                except requests.exceptions.RequestException as req_err:
                    logging.error(f"Error fetching URL {url}: {req_err}")
                    retries -= 1
                    if retries > 0:
                        logging.info(f"Retrying in {backoff_time} seconds...")
                        await asyncio.sleep(backoff_time)
                        backoff_time *= 2  # Exponential backoff

            if retries == 0:
                logging.error(f"Failed to fetch URL {url} after retries")

    return product_urls

async def scrape_product_data(firecrawl_app, url, site_config):
    """Scrapes product data from a given URL using FireCrawl."""
    data = {}

    retries = 3  # Number of retries
    backoff_time = 1  # Initial backoff time in seconds

    while retries > 0:
        try:
            response = firecrawl_app.scrape_url(url=url)
            response.raise_for_status()

            try:
                response_json = response.json()
                html_content = response_json.get('content')
                if not html_content:
                    logging.warning(f"No content found for URL: {url}")
                    return data

                soup = BeautifulSoup(html_content, 'lxml')

                for option_name, selector in site_config['data_selectors']['options'].items():
                    element = soup.select_one(selector)
                    if element:
                        data[option_name] = element.text.strip()

                sku_element = soup.select_one(site_config['data_selectors'].get('sku'))
                if sku_element:
                    data['sku'] = sku_element.text.strip()

                stock_level_element = soup.select_one(site_config['data_selectors'].get('stock_level'))
                if stock_level_element:
                    data['stock_level'] = stock_level_element.text.strip()

                break  # Exit the retry loop if successful

            except json.JSONDecodeError as json_err:
                logging.error(f"JSON decoding error for URL {url}: {json_err}")
                retries -= 1
                if retries > 0:
                    logging.info(f"Retrying in {backoff_time} seconds...")
                    await asyncio.sleep(backoff_time)
                    backoff_time *= 2  # Exponential backoff

        except requests.exceptions.RequestException as req_err:
            logging.error(f"Error fetching URL {url}: {req_err}")
            retries -= 1
            if retries > 0:
                logging.info(f"Retrying in {backoff_time} seconds...")
                await asyncio.sleep(backoff_time)
                backoff_time *= 2  # Exponential backoff

    if retries == 0:
        logging.error(f"Failed to fetch URL {url} after retries")

    return data

async def main():
    config = await load_config('config.json')
    firecrawl_app = FirecrawlApp(api_key='fc-c6bb8011702248109db7d5535e0ed43d')  # Replace with your FireCrawl API key

    product_urls = await get_product_urls(config, firecrawl_app)

    async with aiofiles.open("scraped_products.json", "a") as output_file:
        tasks = []
        for url in product_urls:
            task = scrape_product_data(firecrawl_app, url, config)
            tasks.append(task)

        product_data_list = await asyncio.gather(*tasks)

        for product_data in product_data_list:
            if product_data:
                json_data = json.dumps(product_data)
                await output_file.write(json_data + "\n")

                logging.info(f"Product Name: {product_data.get('name')}")
                logging.info(f"SKU: {product_data.get('sku')}")
                logging.info(f"Stock Level: {product_data.get('stock_level')}")
                logging.info(f"Special Price: {product_data.get('special-price')}")
                logging.info("---")

    logging.info("Scraped product data saved to scraped_products.json")

if __name__ == "__main__":
    asyncio.run(main())

