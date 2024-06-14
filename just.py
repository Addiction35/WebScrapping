import asyncio
import json
from bs4 import BeautifulSoup
from mitmproxy import ctx, http, exceptions

# Global variable to store intercepted URLs
intercepted_urls = set()


class Intercept:
    def __init__(self):
        self.product_urls = []

    def request(self, flow: http.HTTPFlow) -> None:
        intercepted_urls.add(flow.request.url)

    def response(self, flow: http.HTTPFlow) -> None:
        if flow.request.url in intercepted_urls:
            intercepted_urls.remove(flow.request.url)
            self.process_response(flow)

    def process_response(self, flow: http.HTTPFlow) -> None:
        ctx.log.info(f"Intercepted URL: {flow.request.url}")
        ctx.log.info(f"Response Status Code: {flow.response.status_code}")

        # Process only HTML responses (text/html)
        if "text/html" in flow.response.headers.get("content-type", ""):
            try:
                # Parse HTML content using BeautifulSoup
                soup = BeautifulSoup(flow.response.text, "html.parser")

                # Example: Extracting product name from a specific class
                product_name = soup.find("h1", class_="product-title").text.strip()
                ctx.log.info(f"Product Name: {product_name}")

                # Example: Extracting price from a specific CSS selector
                product_price = soup.select_one(".product-price").text.strip()
                ctx.log.info(f"Product Price: {product_price}")

                # Example: Extracting SKU
                sku = soup.find("span", class_="sku").text.strip()
                ctx.log.info(f"SKU: {sku}")

                # You can extract more data as needed using BeautifulSoup selectors

                # Collecting product URLs for later scraping
                self.product_urls.append({
                    'url': flow.request.url,
                    'product_name': product_name,
                    'product_price': product_price,
                    'sku': sku
                })

            except Exception as e:
                ctx.log.error(f"Error parsing response: {e}")

    def save_products_to_file(self):
        with open("scraped_products.json", "w") as f:
            json.dump(self.product_urls, f, indent=4)
        ctx.log.info("Scraped product data saved to scraped_products.json")


addons = [
    Intercept()
]


async def main():
    try:
        await asyncio.sleep(999999)
    except KeyboardInterrupt:
        pass
    intercept.save_products_to_file()


if __name__ == "__main__":
    intercept = Intercept()
    asyncio.run(main())

