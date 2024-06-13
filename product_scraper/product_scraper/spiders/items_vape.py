import scrapy


class ItemsVapeSpider(scrapy.Spider):
    name = "items_vape"
    allowed_domains = ["demandvape.com"]
    start_urls = ["https://demandvape.com"]

    def parse(self, response):
        pass
