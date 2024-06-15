import asyncio
import aiofiles
import json
from bs4 import BeautifulSoup
from firecrawl import FirecrawlApp

async def load_config(filename):
    """Loads the configuration file as a JSON object."""
    async with aiofiles.open(filename, 'r') as f:
        conf = json.loads(await f.read())
        return conf

async def get_product_urls(config, firecrawl_app):
    """Gets product URLs for each category using FireCrawl."""
    product_urls = []

    # Debug: Print the entire config structure
    print("Config structure:", config)

    # Check if 'product-category' exists and is a list
    if 'product-category' not in config or not isinstance(config['product-category'], list):
        raise ValueError("'product-category' must be a list in the configuration file.")

    for category in config['product-category']:
        print(f"Category item: {category}")  # Print the category structure for debugging

        if 'name' not in category or 'selector' not in category:
            print("Invalid category structure, missing 'name' or 'selector'")
            continue

        print(category['name'])

        url = category['selector'].split("'")[1]
        response = firecrawl_app.scrape_url(url=url)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'lxml')

        product_links = soup.find_all('a', class_="product-item-link")

        for link in product_links:
            product_urls.append(link.get('href'))

    return product_urls

async def scrape_product_data(firecrawl_app, url, config):
    """Scrapes product data from a given URL using FireCrawl."""
    data = {}
    response = firecrawl_app.scrape_url(url=url)
    html_content = response.text
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

    return data

async def main():
    config = await load_config('config.json')
    firecrawl_app = FirecrawlApp(api_key='fc-c6bb8011702248109db7d5535e0ed43d')  # Replace with your FireCrawl API key

    product_urls = await get_product_urls(config, firecrawl_app)

    # Open the output file in append mode
    async with aiofiles.open("scraped_products.json", "a") as output_file:
        tasks = []
        for url in product_urls:
            task = scrape_product_data(firecrawl_app, url, config)
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

