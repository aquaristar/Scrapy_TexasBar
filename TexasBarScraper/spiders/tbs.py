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

    name = 'tbs'
    allowed_domains = ['www.texasbar.com']
    start_url = ["https://www.texasbar.com/AM/Template.cfm?Section=Find_A_Lawyer&template=/Customsource/MemberDirectory/MemberDirectoryDetail.cfm&ContactID=%s"] #%s
    #tbRange = [148187, 344000]
    tbRange = [148187, 148200]
    nrbaString = "None Reported By Attorney"
    crawlPages = ['contact', 'about', 'attorney', 'staff', 'firm']

    #Must sync socialMediaDict keys with TexasbarscraperItem() items
    #socialMediaDict = {'Facebook': 'facebook.com', 'Linkedin': 'linkedin.com', 'Avvo': 'avvo.com', 'gPlus': 'plus.google.com', 'Twitter': 'twitter.com'}
    resultData = {}

    #Generate List of Start URLS by iterating through tbRange (The Range of Attorney Profiles on The Texas Bar)
    def __init__(self, *args, **kwargs):
       super(TbsSpider, self).__init__(*args, **kwargs)
       startProfile = self.tbRange[0]
       endProfile = self.tbRange[1]
       while startProfile <= endProfile:
           self.start_urls.append(self.start_url[0] % startProfile)
           startProfile = startProfile + 1

    #Start grabbing attorneys information if it's a valid profile and if they are eligible to practice law.
    def parse(self, response):
        print "-------------------- parse ----------------------------"

        if "page is currently unavailable" in response.body:
            self.logger.info('Profile Not Found. Dropping.')

        eligible = response.xpath("//span[@class='status-text green']")
        if not eligible:
            self.logger.info('Attorney missing eligible status. Dropping.')
            return

        i = TexasbarscraperItem()
        i['Website'] = self.beautify(response.xpath('//a[contains(text(), "VISIT WEBSITE")]/@href').extract())

        i['Phone'] = self.beautify(response.xpath('substring-after(//a[contains(text(), "Tel:")]/@href, "tel:")').extract())
        i['FirstName'] = self.beautify(response.xpath('//span[@class="given-name"]/text()').extract())
        i['LastName'] = self.beautify(response.xpath('//span[@class="family-name"]/text()').extract())
        i['Address'] = self.beautify(response.xpath('//p[@class="address"]/span[1]/text()').extract()) #need to strip tags and merge the list: [Street, City State Zip] structure so far, new [Suite, Street, City State Zip]

        i['PracticeAreas'] = self.beautify(response.xpath('//p[@class="areas"]/text()[2]').extract()) #need to make sure it works for everyone, drop "None Reported By Attorney" and strip tags
        if self.nrbaString in i['PracticeAreas'][0]:
            i['PracticeAreas'] = ""

        i['Company'] = self.beautify(response.xpath('//strong[contains(text(), "Firm:")]/following-sibling::text()').extract())
        if self.nrbaString in i['Company'][0]:
            i['Company'] = ""

        i['AdmissionDate'] = self.beautify(response.xpath('//strong[contains(text(), "TX License Date:")]/following-sibling::text()').extract()) #strip whitespace

        i['Gender'] = self.beautify(response.xpath('//span[@class="honorific-prefix"]/text()').extract())
        if ("Ms" in i['Gender']) or ("Mrs" in i['Gender']):
            i['Gender'] = "Female"
        elif "Mr" in i['Gender']:
            i["Gender"] = "Male"
        else:
            i['Gender'] = "N/A"

        i['Occupation'] = self.beautify(response.xpath('//strong[contains(text(), "Occupation:")]/following-sibling::text()').extract()) #need to strip tags
        i['FirmSize'] = self.beautify(response.xpath('//strong[contains(text(), "Firm Size:")]/following-sibling::text()').extract()) #need to strip tags
        i['PracticeLocation'] = self.beautify(response.xpath('//strong[contains(text(), "Primary Practice Location:")]/following-sibling::text()').extract())  #need to strip tags
        i['Profile'] = response.url

        website = i['Website']
        if self.selectionExists(website):
            page = self.checkScheme(website[0])
            request = Request(page, callback=self.parseWebsite, dont_filter=True)#
            request.meta['Website'] = page
            self.resultData[page]=i
            #print page
            yield request
        else:
            self.logger.info('He has no website information')


    #Load the homepage and store the response, then initiate crawling through the other pages with keywords specified in self.crawlPages
    def parseWebsite(self, response):
        print "----------- parseWebsite ------------"
        key = response.meta['Website']
        i = self.resultData[key]
        #print i
        #return
        rawEmail = response.xpath("substring-after(//a[starts-with(@href, 'mailto:')]/@href, 'mailto:')").extract()
        if self.selectionExists(rawEmail):
            email = self.getEmail(rawEmail)
            if email is not None:
                i['Email'] = email
                self.logger.info("\n\n\n\n\n"+"%s "%key+str(rawEmail)+"  ::: "+email+"\n\n\n\n\n\n")
                self.resultData[key] = i
                return

        del self.resultData[key]
        
        for crawlPage in self.crawlPages:
            rawPages = response.xpath("//a[contains(@href, '"+crawlPage+"')]/@href").extract()
            if self.selectionExists(rawPages):
                for rawPage in rawPages:
                    page = urlparse.urljoin(response.url, rawPage.strip())
                    self.logger.info("Crawling: "+str(page))
                    request = Request(page, callback=self.parseWebsiteMore, dont_filter=True)
                    request.meta['Website'] = page
                    i['Website'] = page
                    self.resultData[page] = i
                    yield request


    #Store all of the responses from crawling in a dict so we can iterate through them later.
    def parseWebsiteMore(self, response):
        print "---- parseWebsiteMore ----"
        key = response.meta['Website']
        i = self.resultData[key]

        rawEmail = response.xpath("substring-after(//a[starts-with(@href, 'mailto:')]/@href, 'mailto:')").extract()        
        if self.selectionExists(rawEmail):
            email = self.getEmail(rawEmail)
            if email is not None:
                i['Website'] = key
                i['Email'] = email
                self.logger.info("\n\n\n\n\n"+"%s "%key+str(rawEmail)+"  ::: "+email+"\n\n\n\n\n\n")                
                self.resultData[key] = i
                return
        print "Dropped"

    def selectionExists(self, selection):
        if selection == []:
            return False
        sel_content = "".join(x.encode('utf-8') for x in selection).strip(' ')
        if sel_content == "":
            return False
        else:
            return True

    def getEmail(self, rawEmail):
        email = rawEmail[0]
        if '?' in email:
            email = re.split("\?", email)
            email = email[0]
        if '@' in email:
            return email
        else:
            return None

    def beautify(self, rawValue):
        process1 = MapCompose(self.__remove_whitespace)
        value = process1(rawValue)
        return value

    def __remove_whitespace(self, value):
        return re.sub("\s{2,}", "", value)

    def checkScheme(self, website):
        urlParts = urlparse.urlparse(website)
        if "www" in urlParts.netloc:
            website = "http://"+ urlParts.netloc + urlParts.path
        else:
            website = "http://www."+ urlParts.netloc + urlParts.path
        return website