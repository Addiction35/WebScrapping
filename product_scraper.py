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
    product_urls = []

    async with aiohttp.ClientSession() as session:
        tasks = []

        for config in configs:
            cookies = {key: value for key, value in (item.split('=') for item in config['cookie'].split('; ') if '=' in item)}  # Parse cookies

            for category in config['product-category']:
                print(f"Scraping category: {category['name']}")
                page = 1

                tasks.append(fetch_category_urls(session, category, cookies, scraperapi_key, page, config, product_urls))

        await asyncio.gather(*tasks)

    return product_urls


async def fetch_category_urls(session, category, cookies, scraperapi_key, page, config, product_urls):
    """Fetches product URLs for a single category page-by-page."""
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
        product_links = soup.select(config['data_selectors']['product_url'])

        if not product_links:
            print(f"No more product links found for category: {category['name']}")
            break

        for link in product_links:
            product_urls.append({
                'url': link.get('href'),
                'config': config,
                'cookies': cookies,
                'scraperapi_key': scraperapi_key
            })

        # Check for next page
        next_page_selector = config.get('selectors', {}).get('next_page')
        next_page = soup.select_one(next_page_selector) if next_page_selector else None

        if not next_page:
            break

        page += 1


async def scrape_product_data(session, product_info):
    """Scrapes product data from a given URL using aiohttp and ScraperAPI."""
    url = product_info['url']
    config = product_info['config']
    cookies = product_info['cookies']
    scraperapi_key = product_info['scraperapi_key']  # Retrieve the scraperapi_key

    scraperapi_url = f"https://api.scraperapi.com?key={scraperapi_key}&url={url}"

    html_content = await fetch(session, scraperapi_url, cookies)
    soup = BeautifulSoup(html_content, 'lxml')

    # Extract product-level data
    try:
        product_data = {
            'product_url': url,
            'product_name': soup.select_one(config['data_selectors']['product_name']).get_text(strip=True) if soup.select_one(config['data_selectors']['product_name']) else None,
            'sku': soup.select_one(config['data_selectors']['sku']).get_text(strip=True) if soup.select_one(config['data_selectors']['sku']) else None,
            'stock_level': soup.select_one(config['data_selectors']['stock_level']).get_text(strip=True) if soup.select_one(config['data_selectors']['stock_level']) else None,
            'wholesale_price': extract_price(soup.select_one(config['data_selectors']['wholesale_price'])) if config['data_selectors'].get('wholesale_price') and soup.select_one(config['data_selectors']['wholesale_price']) else None,
            'product_price': extract_price(soup.select_one(config['data_selectors']['product_price'])) if config['data_selectors'].get('product_price') and soup.select_one(config['data_selectors']['product_price']) else None,
        }
    except Exception as e:
        print(f"Error extracting product-level data for {url}: {e}")
        return {}

    return {url: product_data}


def extract_price(element):
    """Extracts and converts a price from an HTML element."""
    try:
        price_text = element.get_text().strip()
        return float(price_text.replace(',', '').replace('$', ''))
    except ValueError:
        return price_text if price_text else None


async def main():
    configs = load_config('config.json')
    scraperapi_key = "9c8bd768187cf44d42e2b1ddfe117f6a"  # Replace with your ScraperAPI key

    product_urls = await get_product_urls(configs, scraperapi_key)
    processed_urls = set()  # Track processed URLs to avoid duplication

    async with aiohttp.ClientSession() as session:
        async with aiofiles.open("scraped_products.json", "w") as output_file:
            await output_file.write("{\n")  # Start the JSON object

            tasks = []
            for product_info in product_urls:
                url = product_info['url']
                if url in processed_urls:
                    continue  # Skip already processed URLs

                print(f"Scraping product URL: {url}")
                tasks.append(scrape_and_write_product_data(session, product_info, output_file))
                processed_urls.add(url)  # Mark URL as processed

            results = await asyncio.gather(*tasks)

            # Write all data to the file
            first_item = True
            for result in results:
                for url, product_data in result.items():
                    if not first_item:
                        await output_file.write(",\n")
                    await output_file.write(f'"{url}": ')
                    await output_file.write(json.dumps(product_data, indent=4))
                    first_item = False

            await output_file.write("\n}\n")

    print("Scraped product data saved to scraped_products.json")


async def scrape_and_write_product_data(session, product_info, output_file):
    """Scrapes product data and writes it to the file."""
    product_data = await scrape_product_data(session, product_info)
    return product_data


if __name__ == "__main__":
    asyncio.run(main())
