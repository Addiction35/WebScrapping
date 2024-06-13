class ScraperApiProxyMiddleware:
    def __init__(self, scraper_api_key):
        self.scraper_api_key = scraper_api_key

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            scraper_api_key=crawler.settings.get('SCRAPER_API_KEY')
        )

    def process_request(self, request, spider):
        request.meta['proxy'] = f'http://scraperapi:{self.scraper_api_key}@proxy.scraperapi.com:8001'

