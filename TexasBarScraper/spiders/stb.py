# -*- coding: utf-8 -*-
import re
import urlparse
import scrapy
from scrapy.exceptions import CloseSpider
from scrapy.loader.processors import MapCompose
from scrapy.spiders import CrawlSpider, Rule
from TexasBarScraper.items import TexasbarscraperItem
from scrapy.http import Request
from json import loads
import whois


class TbsSpider(CrawlSpider):
    name = 'stb'
    allowed_domains = ['www.texasbar.com']
    start_url = [
        "https://www.texasbar.com/AM/Template.cfm?Section=Find_A_Lawyer&template=/Customsource/MemberDirectory/MemberDirectoryDetail.cfm&ContactID=%s"]  # %s
    tbRange = [148187, 344000]
    nrbaString = "None Reported By Attorney"
    responses = {}
    crawlPages = ['contact', 'about', 'attorney', 'staff', 'firm', 'profiles']

    # Must sync socialMediaDict keys with TexasbarscraperItem() items
    # socialMediaDict = {'Facebook': 'facebook.com', 'Linkedin': 'linkedin.com', 'Avvo': 'avvo.com', 'gPlus': 'plus.google.com', 'Twitter': 'twitter.com'}
    responsiveApi = "http://tools.mercenie.com/responsive-check/api/?format=json&url=%s"

    # Generate List of Start URLS by iterating through tbRange (The Range of Attorney Profiles on The Texas Bar)
    def __init__(self, *args, **kwargs):
        super(TbsSpider, self).__init__(*args, **kwargs)
        startProfile = self.tbRange[0]
        endProfile = self.tbRange[1]
        while startProfile <= endProfile:
            self.start_urls.append(self.start_url[0] % startProfile)
            startProfile = startProfile + 1

    def parse(self, response):
        if "page is currently unavailable" in response.body:
            self.logger.info('Profile Not Found. Dropping.')

        eligible = response.xpath("//span[@class='status-text green']")
        if not eligible:
            self.logger.info('Attorney missing eligible status. Dropping.')
            return

        i = TexasbarscraperItem()
        i['Website'] = self.beautify(response.xpath('//a[contains(text(), "VISIT WEBSITE")]/@href').extract())
        i['FirstName'] = self.beautify(response.xpath('//span[@class="given-name"]/text()').extract())
        i['LastName'] = self.beautify(response.xpath('//span[@class="family-name"]/text()').extract())

        website = i['Website']
        if self.selectionExists(website):
            page = self.checkScheme(website[0])
            request = Request(page, callback=self.parseWebsite, dont_filter=True)
            request.meta['item'] = i
            yield request

    def parseWebsite(self, response):
        i = response.meta['item'] #need to save homepage response, haven't done it yet!
        rawPages = []
        for crawlPage in self.crawlPages:
            crawlLinks = response.xpath("//a[contains(@href, '" + crawlPage + "')]/@href").extract()
            rawPages.extend(crawlLinks)
        if self.selectionExists(rawPages):
            for rawPage in rawPages:
                page = urlparse.urljoin(response.url, rawPage.strip())
                self.logger.info("Crawling: "+str(page))
                request = Request(page, callback=self.storeResponses, dont_filter=True)
                request.meta['item'] = i
                yield request
        i['responses'] = self.responses
        self.responses = {}
        yield i

    def storeResponses(self, response):
        url = response.url
        self.responses[url] = response

    # def findEmail(self, i):
    #     responses = i['responses']
    #     emailList = []
    #     for url, response in responses.iteritems():
    #         rawEmail = response.xpath("substring-after(//a[starts-with(@href, 'mailto:')]/@href, 'mailto:')").extract()
    #         if self.selectionExists(rawEmail):
    #             emailList.extend(rawEmail)
    #         if self.selectionExists(emailList):
    #             email = max(emailList, key=emailList.count)
    #             self.logger.info("\n\n\n\n\n" + str(email) + "\n\n\n\n\n\n")
    #             self.format_email(rawEmail, i)
    #     return i
    #
    # def format_email(self, rawEmail, i):
    #     email = rawEmail[0]
    #     if '?' in email:
    #         email = re.split("\?", email)
    #         email = email[0]
    #     if '@' in email:
    #         i['Email'] = email
    #     return i

    def selectionExists(self, selection):
        if type(selection) is list and selection:
            return True
        return False

    def beautify(self, rawValue):
        process1 = MapCompose(self.__remove_whitespace)
        value = process1(rawValue)
        return value

    def __remove_whitespace(self, value):
        return re.sub("\s{2,}", "", value)

    def checkScheme(self, website):
        urlParts = urlparse.urlparse(website)
        website = "http://" + urlParts.netloc + urlParts.path
        return website