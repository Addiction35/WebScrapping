import scrapy


class ProductsSpider(scrapy.Spider):
    name = "products"
    allowed_domains = ["1oakwholesale.com"]
    start_urls = ["https://1oakwholesale.com"]

    for url in startrt_urls:
        yield.scrapy.Requests(
                url = url
                callback=self.parse,
                meta={"proxy": "http://221.140.237.231:5002"},
                )

    def parse(self, response):
        pass
