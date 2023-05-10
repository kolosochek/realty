from grab import Grab, GrabError, GrabNetworkError, GrabTimeoutError
import math
import re
import locale
from datetime import datetime
from urllib.parse import urlencode
import pycurl
import json
from html import unescape
from .models import RealtyAd, Image


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
            raw_int = "".join(re.findall('\d*', value.strip()))
            if raw_int:
                return int(raw_int)
        except (ValueError, BaseException) as error:
            if self.debug:
                print("Can't parse int from value=%s, reason: %s" % (value, error))
            return 0

    # send request and catch all exceptions
    def safe_send_request(self, url, update_html=True, method="GET"):
        try:
            response = self.grab.request(url=url, method=method)
            if update_html:
                self.html = response.build_html_tree()
            else:
                return response.build_html_tree()

        except (GrabError, GrabNetworkError, GrabTimeoutError) as error:
            print("Can't fetch an url %s, reason: %s" % (url, error))

    def get_ad_contacts(self, ad_url=None, ad_id=None):
        c = pycurl.Curl()
        # debug
        if self.debug:
            if ad_url is None:
                ad_url = 'https://sale-me.com/budva/rent-hire/flat/otlichnaja-kvartira-studija-v-budve-204742.html'
            if ad_id is None:
                ad_id = 204742
        c.setopt(c.URL, "%s?bff=ajax&s=bbs&act=item-contacts" % ad_url)
        post_data = {'page': 'view', 'id': '%s' % int(ad_id)}
        postfields = urlencode(post_data)
        c.setopt(c.POSTFIELDS, postfields)
        raw_json = c.perform_rs()
        c.close()
        return raw_json

    def get_ad_item(self, ad_item):
        # convert locale to RU coz we need to parse Cyrillic month names
        locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
        date_created_selector = ".l-main__content .v-info small"
        html = self.safe_send_request(ad_item["url"], False)

        date_created_node = html.cssselect(date_created_selector)[0]
        images_node = html.cssselect("#j-view-images div")
        address_node = html.cssselect("p.v-descr_address .v-descr_address_val")[0] if len(html.cssselect("p.v-descr_address .v-descr_address_val")) else ""
        long_description_node = html.cssselect("div.v-descr_text")[0]
        ad_author_node = html.cssselect("div.v-descr_contact_user")[0] if len(html.cssselect("div.v-descr_contact_user")) else ""

        ad_item["date_posted"] = date_created_node.text_content().strip().split(" | ")[::-1][0].split(",")[0].split(": ")[::-1][0]
        ad_item["ad_id"] = "".join(re.findall('\d+.html', self.grab.config["url"])).replace(".html", "")
        ad_item["thumbnails"] = []
        ad_item["images"] = []
        ad_item["address"] = address_node.text_content().replace("показать на карте", "").strip()[:-1] if len(address_node) else ""
        ad_item["long_description"] = long_description_node.text_content().strip()
        ad_item["ad_author"] = ad_author_node.text_content().strip()
        try:
            data = json.loads(self.get_ad_contacts(ad_url=self.grab.config["url"], ad_id=ad_item["ad_id"]))
            if "data" in data:
                if "phones" in data["data"]:
                    ad_item["phones"] = data["data"]["phones"]
                if "contacts" in data["data"]:
                    if "viber" in data["data"]["contacts"]:
                        ad_item["viber"] = data["data"]["contacts"]["viber"]
                    if "telegram" in data["data"]["contacts"]:
                        ad_item["telegram"] = data["data"]["contacts"]["telegram"]
                    if "whatsapp" in data["data"]["contacts"]:
                        ad_item["whatsapp"] = data["data"]["contacts"]["whatsapp"]

        except BaseException as error:
            print("Can't get ad %s item contacts, reason: %s" % (self.grab.config["url"], error))
        try:
            ad_item["date_posted"] = datetime.strptime(ad_item["date_posted"], '%d %b %Y')
        except ValueError:
            ad_item["date_posted"] = datetime.today()
        # images
        if len(images_node):
            for image in images_node:
                if "data-img" in image.attrib:
                    ad_item["images"].append(image.attrib["data-img"])
                    ad_item["thumbnails"].append(image.attrib["data-thumb"])

        if self.debug:
            print(ad_item)


        # get realty ad object and update it
        ad_object = RealtyAd.objects.get(
            url=ad_item["url"]
        )
        if len(ad_item["address"]):
            ad_object.address = ad_item["address"]
        # contacts
        if "viber" in ad_item:
            ad_object.viber = unescape(ad_item["viber"])
        if "telegram" in ad_item:
            ad_object.telegram = unescape(ad_item["telegram"])
        if "whatsapp" in ad_item:
            ad_object.whatsapp = unescape(ad_item["whatsapp"])
        if "phones" in ad_item:
            ad_object.phones = unescape(ad_item["phones"])

        ad_object.ad_id = ad_item["ad_id"]
        ad_object.long_description = ad_item["long_description"]
        if len(ad_item["ad_author"]):
            ad_object.ad_author = ad_item["ad_author"]
        for image_url in ad_item['images']:
            image_object = Image(url=image_url, source=image_url, thumbnail=ad_item["thumbnail"])
            image_object.save()
            # push image to images arr
            ad_object.images.add(image_object)
        ad_object.save()

    def get_ad_list_items(self, html):
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
        short_description_node = item.cssselect("div.sr-2-item-desc")
        city_node = item.cssselect(".sr-2-item-address")[0]

        ad["type"] = self.source["realtyParams"]["type"]
        ad["title"] = title_node.text_content().strip()
        ad["url"] = title_node.attrib["href"]
        ad["thumbnail"] = thumbnail_node.attrib["src"]
        ad["price"] = self.safe_int(price_node.text_content())
        ad["short_description"] = short_description_node[0].text_content().strip() if len(short_description_node) else ''
        ad["city"] = city_node.text_content().strip()


        # create django model object
        ad_object = RealtyAd.objects.get_or_create(
            url=ad["url"],
            title=ad["title"],
            type=ad["type"],
            thumbnail=ad["thumbnail"],
            price=ad["price"],
            short_description=ad["short_description"],
            city=ad["city"]
        )

        # if object created
        # if ad_object[1]
            # pass
        # goto ad url and parse detail ad info
        self.get_ad_item(ad)

    def parse_page(self, page):
        # get html
        self.safe_send_request(
            "%s%s/?page=%s" % (self.source["sourceBaseUrl"], self.source["realtyParams"]["type"], page))
        # parse page valuable info
        self.get_ad_list_items(self.html)

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
        for page in range(1, self.source["realtyParams"]["pagesTotal"]):
            if self.debug:
                print("Parsing page %s of %s" % (page, self.source["realtyParams"]["pagesTotal"]))
            self.parse_page(page)
