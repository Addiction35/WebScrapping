import aiohttp
import asyncio
import aiofiles
import json
from bs4 import BeautifulSoup


def load_config(filename):
    """Loads the configuration file as a JSON object."""
    with open(filename, 'r') as f:
        conf = json.load(f)
    return conf


async def fetch(session, url, cookies):
    """Fetches the content of a URL using aiohttp."""
    async with session.get(url, cookies=cookies) as response:
        return await response.text()


async def get_product_urls(configs, scraperapi_key):
    """Gets product URLs for each category using aiohttp and ScraperAPI."""
    product_urls = set()  # Use a set to avoid duplicate URLs

    async with aiohttp.ClientSession() as session:
        for config in configs:
            cookies = {key: value for key, value in (item.split('=') for item in config['cookie'].split('; '))}  # Parse cookies

            for category in config['product-category']:
                print(f"Scraping category: {category['name']}")
                page = 1

                while True:
                    url = category['selector']
                    if "'" in url:
                        url = url.split("'")[1]
                    elif '"' in url:
                        url = url.split('"')[1]

                    paginated_url = f"{url}?p={page}"
                    scraperapi_url = f"https://api.scraperapi.com?key={scraperapi_key}&url={paginated_url}"

                    html_content = await fetch(session, scraperapi_url, cookies)
                    soup = BeautifulSoup(html_content, 'lxml')
                    product_links = soup.find_all('a', class_="product-item-link")

                    if not product_links:
                        print(f"No more product links found for category: {category['name']}")
                        break

                    for link in product_links:
                        product_urls.add(link.get('href'))  # Add to set

                    # Check for next page
                    next_page = soup.select_one(config['selectors']['next_page'])
                    if not next_page:
                        break

                    page += 1

    return list(product_urls)  # Convert set back to list


async def scrape_product_data(session, url, config, scraperapi_key):
    """Scrapes product data from a given URL using aiohttp and ScraperAPI."""
    cookies = {key: value for key, value in (item.split('=') for item in config['cookie'].split('; '))}  # Parse cookies
    scraperapi_url = f"https://api.scraperapi.com?key={scraperapi_key}&url={url}"

    html_content = await fetch(session, scraperapi_url, cookies)
    soup = BeautifulSoup(html_content, 'lxml')

    # Extract product-level data
    try:
        product_data = {
            'product_url': url,
            'product_name': soup.select_one(config['data_selectors']['product_name']).text.strip() if soup.select_one(config['data_selectors']['product_name']) else None,
            'sku': soup.select_one(config['data_selectors']['sku']).text.strip() if soup.select_one(config['data_selectors']['sku']) else None,
            'stock_level': soup.select_one(config['data_selectors']['stock_level']).text.strip() if soup.select_one(config['data_selectors']['stock_level']) else None,
            'special_price': soup.select_one(config['data_selectors']['special_price']).text.strip() if soup.select_one(config['data_selectors']['special_price']) else None
        }
    except Exception as e:
        print(f"Error extracting product-level data for {url}: {e}")
        return []

    data = []
    # Loop through the options
    options = soup.select(config['data_selectors']['options']['name'])
    for option in options:
        option_data = product_data.copy()  # Copy product-level data to each option
        for key, value in config['data_selectors']['options'].items():
            try:
                element = option.select_one(value)
                if element:
                    option_data[key] = element.text.strip()
                else:
                    print(f"No match found for {key} using selector {value}")
                    option_data[key] = None
            except Exception as e:
                print(f"Error extracting {key} for {url}: {e}")
                option_data[key] = None

        data.append(option_data)

    return data


async def main():
    configs = load_config('config.json')
    scraperapi_key = "9c8bd768187cf44d42e2b1ddfe117f6a"  # Replace with your ScraperAPI key

    product_urls = await get_product_urls(configs, scraperapi_key)
    all_products = []
    processed_urls = set()  # Track processed URLs to avoid duplication

    async with aiohttp.ClientSession() as session:
        async with aiofiles.open("scraped_products.json", "w") as output_file:
            await output_file.write("[\n")  # Start the JSON array

            for url in product_urls:
                if url in processed_urls:
                    continue  # Skip already processed URLs

                print(f"Scraping product URL: {url}")
                product_data = await scrape_product_data(session, url, configs[0], scraperapi_key)  # Use the first config for scraping data
                all_products.extend(product_data)
                processed_urls.add(url)  # Mark URL as processed

                for product in product_data:
                    print(f"Product Name: {product.get('product_name')}")
                    print(f"SKU: {product.get('sku')}")
                    print(f"Stock Level: {product.get('stock_level')}")
                    print(f"Special Price: {product.get('special_price')}")
                    print("---")

                    # Write product data to file
                    await output_file.write(json.dumps(product, indent=4))
                    await output_file.write(",\n")

            # Remove the last comma and close the JSON array
            await output_file.seek(output_file.tell() - 2, 0)
            await output_file.write("\n]\n")

    print("Scraped product data saved to scraped_products.json")


if __name__ == "__main__":
    asyncio.run(main())

