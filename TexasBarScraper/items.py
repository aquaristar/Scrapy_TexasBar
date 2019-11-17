# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field, Item


class TexasbarscraperItem(scrapy.Item):
    Website = Field()
    Phone = Field()
    FirstName = Field()
    LastName = Field()
    Address = Field()
    PracticeAreas = Field()
    Company = Field()
    AdmissionDate = Field()
    Gender = Field()
    Occupation = Field()
    FirmSize = Field()
    PracticeLocation = Field()
    Email = Field()
    Facebook = Field()
    Linkedin = Field()
    Avvo = Field()
    gPlus = Field()
    Twitter = Field()
    Responsive = Field()
    MobileSpeed = Field()
    MobileUsability = Field()
    DesktopSpeed = Field()
    Doctype = Field()
    Profile = Field()
    responses = Field()
    pass


