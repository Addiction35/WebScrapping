import scrapy
import json
import logging
from bs4 import BeautifulSoup
from scrapy.http import HtmlResponse
from Neew.items import ProductItem

logging.basicConfig(level=logging.INFO)  # Set logging level to INFO

# Rate limiting parameters
REQUESTS_PER_MINUTE = 60  # Adjust as per your rate limit requirements

class FirecrawlSpider(scrapy.Spider):
    name = 'firecrawl'
    allowed_domains = ['1oakwholesale.com', 'demandvape.com']
    start_urls = [
        'https://1oakwholesale.com',
        'https://demandvape.com',
    ]

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,  # Limit concurrent requests
        'DOWNLOAD_DELAY': 60 / REQUESTS_PER_MINUTE,  # Set download delay to respect rate limit
        'LOG_LEVEL': 'INFO',
    }

    def parse(self, response):
        logging.info(f"Processing site: {response.url}")

        # Define your configuration or load it from a file
        config = [
            {
                'url': 'https://1oakwholesale.com',
                'product-category': [
                    {'name': 'Devices', 'selector': "your-selector-for-devices"},
                    {'name': 'E-Juice', 'selector': "your-selector-for-ejuice"},
                    {'name': 'Disposables', 'selector': "your-selector-for-disposables"},
                    {'name': 'Delta', 'selector': "your-selector-for-delta"},
                ]
            },
            {
                'url': 'https://demandvape.com',
                'product-category': [
                    {'name': 'Devices', 'selector': "your-selector-for-devices"},
                    {'name': 'E-Juice', 'selector': "your-selector-for-ejuice"},
                ]
            }
        ]

        # Loop through configuration to extract product URLs
        for site_config in config:
            for category in site_config['product-category']:
                logging.info(f"Category: {category['name']}")
                url = category['selector']

                yield scrapy.Request(
                    url=url,
                    callback=self.parse_product_urls,
                    meta={'category': category['name'], 'site_url': site_config['url']}
                )

    def parse_product_urls(self, response):
        category = response.meta['category']
        site_url = response.meta['site_url']

        logging.info(f"Processing {category} on {site_url}")

        try:
            response_json = json.loads(response.text)
            html_content = response_json.get('content', '')
            soup = BeautifulSoup(html_content, 'html.parser')

            product_links = soup.find_all('a', class_="product-item-link")

            for link in product_links:
                product_url = link.get('href')
                yield scrapy.Request(
                    url=product_url,
                    callback=self.parse_product_data,
                    meta={'category': category, 'site_url': site_url}
                )

        except json.JSONDecodeError as json_err:
            logging.error(f"JSON decoding error: {json_err}")

    def parse_product_data(self, response):
        category = response.meta['category']
        site_url = response.meta['site_url']

        logging.info(f"Scraping product data from {response.url}")

        try:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract product data using BeautifulSoup or other parsers
            product_name = soup.find('h1', class_='product-name').text.strip()
            sku = soup.find('span', class_='product-sku').text.strip()
            stock_level = soup.find('div', class_='stock-level').text.strip()

            # Create and yield an item
            item = ProductItem()
            item['category'] = category
            item['site_url'] = site_url
            item['product_name'] = product_name
            item['sku'] = sku
            item['stock_level'] = stock_level

            yield item

        except Exception as e:
            logging.error(f"Error scraping {response.url}: {e}")
