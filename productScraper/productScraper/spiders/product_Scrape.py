import scrapy
from scrapy.spiders import CrawlSpider
import json
import os
from productScraper.scraperapi_middleware import ScraperApiProxyMiddleware

class ProductScraper(CrawlSpider):
    name = "product_scraper"
    allowed_domains = ["1oakwholesale.com"]

    def __init__(self, config_file="config.json", cookie=None, *args, **kwargs):
        super(ProductScraper, self).__init__(*args, **kwargs)
        self.config = self._load_config(config_file)
        self.start_urls = [self.config["base_url"]]
        self.cookies = {"DEV_PHPSESSID": cookie} if cookie else None

    def _load_config(self, config_file):
        """Loads the configuration file as a JSON object."""
        with open(config_file, 'r') as f:
            conf = json.load(f)
        return conf

    def start_requests(self):
        """Fetches and parses initial category pages."""
        for category in self.config["product-category"]:
            # Construct complete URL using base URL
            category_url = f"https://1oakwholesale.com/vape/devices.html"
            print(category_url)
            yield scrapy.Request(url=category_url, callback=self.parse_category, meta={"category_name": category["name"]})

    def parse_category(self, response):
        """Parses category page and extracts product links."""
        category_name = response.meta["category_name"]
        product_links = response.css(self.config["data_selectors"]["product_url"]).xpath("@href").extract()

        for product_link in product_links:
            yield scrapy.Request(url=product_link, callback=self.parse_product, meta={"category": category_name})

        next_page_url = response.css(self.config["data_selectors"]["next_page"]).xpath("@href").get()
        if next_page_url:
            yield scrapy.Request(url=next_page_url, callback=self.parse_category, meta={"category_name": category_name})

    def parse_product(self, response):
        """Parses product page and extracts product details."""
        product_data = {}
        product_data["category"] = response.meta["category"]
        product_data["name"] = response.css(self.config["data_selectors"]["product_name"]).get().strip() if response.css(self.config["data_selectors"]["product_name"]).get() else None
        product_data["sku"] = response.css(self.config["data_selectors"]["sku"]).get().strip() if response.css(self.config["data_selectors"]["sku"]).get() else None
        product_data["stock_level"] = response.css(self.config["data_selectors"]["stock_level"]).get().strip() if response.css(self.config["data_selectors"]["stock_level"]).get() else None
        product_data["wholesale_price"] = response.css(self.config["data_selectors"]["special_price"]).get().strip() if response.css(self.config["data_selectors"]["special_price"]).get() else None

        # Extract data for each product option
        options = response.css(self.config["data_selectors"]["options"])
        product_data["options"] = []

        for option in options:
            option_data = {}
            option_data["name"] = option.css(self.config["data_selectors"]["options"]["name"]).get().strip() if option.css(self.config["data_selectors"]["options"]["name"]).get() else None
            option_data["product-id"] = option.css(self.config["data_selectors"]["options"]["product-id"]).attrib.get("data-product-id")
            option_data["special_price"] = option.css(self.config["data_selectors"]["options"]["special_price"]).get().strip() if option.css(self.config["data_selectors"]["options"]["special_price"]).get() else None
            option_data["stock_level"] = option.css(self.config["data_selectors"]["options"]["stock_level"]).get().strip() if option.css(self.config["data_selectors"]["options"]["stock_level"]).get() else None

            product_data["options"].append(option_data)

        yield product_data

