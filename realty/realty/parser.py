import math
import re
from grab import Grab, GrabError, GrabNetworkError, GrabTimeoutError
from .models import RealtyAd


class RealtyParser:
    debug = True
    urlDict = [{
        'sourceType': "sales.me",
        'sourceBaseUrl': "https://sale-me.com/montenegro/rent-hire/",
        "realtyParams": {
            "type": "flat",
            "index": 0,
            "pagesTotal": 0,
            "adsTotal": 0,
        },
    }]
    html = None
    source = {}
    adCategoryPerPage = 40
    adCategoryTotalSelector = "div.f-categories"
    adListItemSelector = "div.sr-2-list-item-n"
    adListItemTitleSelector = "div.sr-2-list-item-n-title a"
    adCategoryListNodeSelector = "#j-f-categories-block .f-categories-col-count"

    def __init__(self):
        self.grab = Grab()
        for source in self.urlDict:
            self.source = source
            self.parse_ad()

    def safe_int(self, value):
        try:
            raw_int = re.match(r'^\d*', value.replace(" ", ""))
            if raw_int:
                return int(raw_int[0])
        except (ValueError, BaseException) as error:
            if self.debug:
                print("Can't parse int from value=%s, reason: %s" % (value, error))
            return 0

    def safe_send_request(self, url):
        # send request
        try:
            response = self.grab.request(
                "%s" % url)
            self.html = response.build_html_tree()

        except (GrabError, GrabNetworkError, GrabTimeoutError) as error:
            print("Can't fetch an url %s, reason: %s" % (url, error))

    def get_ad_items(self, html):
        ad_list_items = html.cssselect(RealtyParser.adListItemSelector)
        if len(ad_list_items):
            for item in ad_list_items:
                self.get_list_item(item)
        else:
            return BaseException("No ad list items found!")

    def get_list_item(self, item):
        ad = {}
        title_node = item.cssselect(self.adListItemTitleSelector)[0]
        thumbnail_node = item.cssselect("img")[0]
        price_node = item.cssselect(".sr-2-list-item-n-price")[0]
        short_description_node = item.cssselect(".sr-2-item-desc")[0] if len(item.cssselect(".sr-2-item-desc")) else False
        city_node = item.cssselect(".sr-2-item-address")[0]

        ad["type"] = self.source["realtyParams"]["type"]
        ad["title"] = title_node.text_content().strip()
        ad["url"] = title_node.attrib["href"]
        ad["thumbnail"] = thumbnail_node.attrib["src"]
        ad["price"] = self.safe_int(price_node.text_content().strip())
        ad["short_description"] = short_description_node.text_content().strip() if short_description_node else ''
        ad["city"] = city_node.text_content().strip()


        # create django model object
        ad_object = RealtyAd(
            url=ad["url"],
            title=ad["title"],
            type=ad["type"],
            thumbnail=ad["thumbnail"],
            price=ad["price"],
            short_description=ad["short_description"],
            city=ad["city"]
        )
        # and save it fur teh justice
        ad_object.save()

        if self.debug:
            print("ad")
            print(ad)

    def parse_page(self, page):
        # get html
        self.safe_send_request(
            "%s%s/?page=%s" % (self.source["sourceBaseUrl"], self.source["realtyParams"]["type"], page))
        # parse page valuable info
        self.get_ad_items(self.html)

    def parse_source_params(self):
        def set_category_params(node):
            self.source["realtyParams"]["adsTotal"] = self.safe_int(node[self.source["realtyParams"]["index"]].text_content())
            self.source["realtyParams"]["pagesTotal"] = math.ceil(self.source["realtyParams"]["adsTotal"] / self.adCategoryPerPage)

            if self.debug:
                # debug
                print("Total ads in category %s is: %s" % (self.source["realtyParams"]["type"], self.source["realtyParams"]["adsTotal"]))
                print("Total pages in category %s is: %s" % (self.source["realtyParams"]["type"], self.source["realtyParams"]["pagesTotal"]))

        if self.html is None:
            self.safe_send_request(self.source["sourceBaseUrl"])

        # get total category ads
        category_list_node = self.html.cssselect(self.adCategoryListNodeSelector)
        if len(category_list_node):
            set_category_params(category_list_node)
        else:
            return BaseException("category_list_node is empty!")

    def parse_ad(self):
        # debug
        print("Starting to parse source %s, at url: %s" % (self.source['sourceType'], self.source['sourceBaseUrl']), )

        # get source params like total ads, total pages, etc
        if not self.source["realtyParams"]["pagesTotal"]:
            self.parse_source_params()

        # iterate through all pages, one by one
        # for page in range(1, 2):
        #for page in range(1, self.source["realtyParams"]["pagesTotal"]):
        for page in range(1, 2):
            if self.debug:
                print("Parsing page %s of %s" % (page, self.source["realtyParams"]["pagesTotal"]))
            self.parse_page(page)
