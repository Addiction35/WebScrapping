# importing the scrapy
import scrapy

class ImdbSpider(scrapy.Spider):
    name = "imdb"
    allowed_domains = ["imdb.com"]
    start_urls = ['http://www.imdb.com/chart/top',]
   
    def parse(self, response):
        # table coloums of all the movies 
        columns = response.css('table[data-caller-name="chart-top250movie"] tbody[class="lister-list"] tr')
        for col in columns:
            # Get the required text from element.
            yield {
                "title": col.css("td[class='titleColumn'] a::text").extract_first(),
                "year": col.css("td[class='titleColumn'] span::text").extract_first().strip("() "),
                "rating": col.css("td[class='ratingColumn imdbRating'] strong::text").extract_first(),

            }
