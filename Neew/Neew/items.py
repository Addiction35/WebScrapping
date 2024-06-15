# File: my_project_name/my_project_name/items.py

import scrapy

class ProductItem(scrapy.Item):
    category = scrapy.Field()
    site_url = scrapy.Field()
    product_name = scrapy.Field()
    sku = scrapy.Field()
    stock_level = scrapy.Field()
    special_price = scrapy.Field()
    # Add more fields as needed

