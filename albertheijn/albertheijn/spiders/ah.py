import json

import scrapy
from scrapy import Request


class AhSpider(scrapy.Spider):
    name = 'ah'
    allowed_domains = ['www.ah.nl']
    start_urls = ['https://www.ah.nl/allerhande/recepten']

    custom_settings = {'ROBOTSTXT_OBEY': False, 'LOG_LEVEL': 'INFO',
                       'CONCURRENT_REQUESTS_PER_DOMAIN': 5,
                       'RETRY_TIMES': 5,
                       'DOWNLOADER_MIDDLEWARES': {'scrapy_zyte_smartproxy.ZyteSmartProxyMiddleware': 610},
                       'ZYTE_SMARTPROXY_ENABLED': True,
                       'ZYTE_SMARTPROXY_APIKEY': '15cf7b06d9eb49cd971fadeba28db14a',
                       'FEED_URI': 'recepie.csv',
                       'FEED_FORMAT': 'csv',
                       }

    def parse(self, response):
        # recepies_themes = response.xpath(
        #     "//div[cont
        recepies_themes = response.xpath(
            "//div[contains(@class,'grid_gridCollapse')]/div[@class='row']/div/div[contains(@class,'theme-lister-card_root')]/div[contains(@class,'theme-lister-card_content')]/div")
        for recepies_theme in recepies_themes:
            recepie_theme_name = recepies_theme.xpath("./a/h3/text()").get()
            recepie_theme_link = recepies_theme.xpath("./a/@href").get()
            recepie_nodes = response.xpath(
                "//section[@id='" + str(recepie_theme_link).lstrip(
                    '#') + "']//div[contains(@class,'row content-list-link-groups_row')][2]//a[contains(@class,'content-list-link-group_linkAnchor') and contains(@href,'recepten') and not(contains(text(),'Alle'))]")
            for recepie_category in recepie_nodes:
                recepie_category_name = recepie_category.xpath("./text()").get()
                recepie_category_url = recepie_category.xpath("./@href").get()
                if not recepie_category_url.startswith(self.allowed_domains[0]):
                    recepie_category_url = 'https://' + self.allowed_domains[0] + recepie_category_url

                yield Request(recepie_category_url, self.parse_recepie, meta={
                    'recepie_theme': recepie_theme_name,
                    'recepie_category': recepie_category_name
                })

    def parse_recepie(self, response):
        recepies_themes = response.meta['recepie_theme']
        recepies_category = response.meta['recepie_category']
        recepie_urls = response.xpath("//a[@role='link']/@href").extract()
        for recepie_urls in recepie_urls:
            if not recepie_urls.startswith(self.allowed_domains[0]):
                recepie_urls = 'https://' + self.allowed_domains[0] + recepie_urls
            yield Request(recepie_urls, self.parser_recepie_detail, meta={
                'recepie_theme': recepies_themes,
                'recepie_category': recepies_category
            })

        next_page_url = response.xpath(
            "//*[contains(@class,'pagination_current__mA+EX')]/ancestor::li/following-sibling::li[1]/a/@href").get()
        if next_page_url:
            if not next_page_url.startswith(self.allowed_domains[0]):
                next_page_url = 'https://' + self.allowed_domains[0] + next_page_url
            yield Request(next_page_url, self.parse_recepie, meta={
                'recepie_theme': recepies_themes,
                'recepie_category': recepies_category
            })

    def parser_recepie_detail(self, response):
        global key
        recepie_id = response.request.url.split('R-R')[1].split('/')[0]
        recepie_json_str = response.text.split("window.__APOLLO_STATE__= ")[1].strip().split("window.__MEMBER__")[0]
        recepie_json = json.loads(recepie_json_str)
        recepie_detail = recepie_json['Recipe:{}'.format(recepie_id)]

        try:
            recipe_images = recepie_detail['imageRenditions']['d612x450']['url']
        except:
            recipe_images = ''
        try:
            recipe_description = recepie_detail['description']
        except:
            recipe_description = ''

        # Number_of_Person_Default
        try:
            steps = recepie_detail['preparation']['steps']
        except:
            steps = ''
        try:
            recipe_name = recepie_detail['title']
        except:
            recipe_name = ''
        try:
            prep_time = recepie_detail['ovenTime']
        except:
            prep_time = ''
        try:
            cook_time = recepie_detail['cookTime']
        except:
            cook_time = ''
        try:
            total_time = recepie_detail['waitTime']
        except:
            total_time = ''
        try:
            serv_size = recepie_detail['servings']['number']
        except:
            serv_size = ''
        ingredients = recepie_detail['ingredients']
        ingredients_list = []
        for ingredient in ingredients:
            ingredient_id = ingredient.get('__ref', None)
            ingredient_name = recepie_json[str(ingredient_id)]['name']['singular']
            ingredient_quantity_unit = recepie_json[str(ingredient_id)]['quantityUnit']['singular']
            ingredient_quantity = recepie_json[str(ingredient_id)]['quantity']
            ingredients_list.append([ingredient_name, ingredient_quantity_unit, ingredient_quantity])
        try:
            recipe_category = response.meta['recepie_category']
        except:
            recipe_category = ''
        try:
            recipe_cuisine = recepie_detail['cuisines']
        except:
            recipe_cuisine = ''
        try:
            rating_value = recepie_detail['rating']['average']
        except:
            rating_value = ''
        try:
            rating_count = recepie_detail['rating']['count']
        except:
            rating_count = ''
        nutritions_list = []
        nutritions = recepie_detail['nutritions'].keys()
        for key in nutritions:
            if '__typename' == key:
                continue
            else:
                try:
                    nutrition = recepie_detail['nutritions'][key]['name'] + " " + str(
                        recepie_detail['nutritions'][key]['value']) + " " + \
                                recepie_detail['nutritions'][key]['unit']
                except:
                    nutrition = ''
                nutritions_list.append(nutrition)
        recipe_url = recepie_detail['href']
        # Season
        meal_type = ','.join(recepie_detail['courses'])
        # MealCat
        try:
            recepie_kal = recepie_detail['nutritions']['energy']['value']
        except:
            recepie_kal = ''

        try:
            recip_themes = response.meta['recepie_theme']
        except:
            recip_themes = ''
        tags_list = []
        for recepie_tag in recepie_detail['tags']:
            tag_name = recepie_tag['key']
            tag_value = recepie_tag['value']
            tags_list.append(tag_name + ": " + tag_value)

        item = dict()
        item['recipe_name'] = recipe_name
        item['recepie_id'] = recepie_id
        item['recipe_images'] = recipe_images
        item['recipe_description'] = recipe_description
        item['recipe_url'] = self.allowed_domains[0] + recipe_url
        item['recip_themes'] = recip_themes
        item['recipe_category'] = recipe_category
        item['meal_type'] = meal_type
        item['steps'] = steps
        item['tags'] = ','.join(tags_list)
        item['serv_size'] = serv_size
        item['prep_time'] = prep_time
        item['cook_time'] = cook_time
        item['total_time'] = total_time
        try:
            item["spicy"] = response.xpath("//span[contains(@class,'spiciness_text')]/text()").get()
        except:
            item["spicy"] = ''
        col_no = 1
        for ingredient in ingredients_list:
            item["ingredient name {}".format(col_no)] = ingredient[0]
            item["qty {}".format(col_no)] = str(ingredient[2]) + " " + ingredient[1]
            col_no += 1
        item['rating_value'] = rating_value
        item['rating_count'] = rating_count
        item['nutritions'] = ','.join(nutritions_list)
        item['recepie_kal'] = recepie_kal
        item['recipe_cuisine'] = recipe_cuisine
        yield item
