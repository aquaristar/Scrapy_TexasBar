# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html
from scrapy.exceptions import DropItem

import re

class TexasbarscraperPipeline(object):

    ids_seen = set()

    def process_item(self, i, spider):

        self.findEmail(i, spider)

        # if 'Email' in item.keys():
        #     email = item['Email']
        #     if email in self.ids_seen:
        #         #log.msg(self.ids_seen.__str__())
        #         raise DropItem("Duplicate Email")
        #     else:
        #         #log.msg("Added Email to Seen List: " +email)
        #         item['Email'] = item['Email'].lower()
        #         self.ids_seen.add(email)
        # else:
        #     raise DropItem("Missing Email:")
        return i

    def selectionExists(self, selection):
        if type(selection) is list and selection:
            return True
        return False

    def findEmail(self, i, spider):
        responses = i['responses']
        emailList = []
        for url, response in responses.iteritems():
            rawEmail = response.xpath("substring-after(//a[starts-with(@href, 'mailto:')]/@href, 'mailto:')").extract()
            if self.selectionExists(rawEmail):
                emailList.extend(rawEmail)
            if self.selectionExists(emailList):
                email = max(emailList, key=emailList.count)
                spider.logger.info("\n\n\n\n\n" + str(email) + "\n\n\n\n\n\n")
                self.format_email(rawEmail, i)
        return i

    def format_email(self, rawEmail, i):
        email = rawEmail[0]
        if '?' in email:
            email = re.split("\?", email)
            email = email[0]
        if '@' in email:
            i['Email'] = email
        return i
