#!/usr/bin/python
# -*- coding: utf-8 -*-

from rss_parser import RSSParser
from requests import get
from dateutil import parser
from datetime import datetime
import atoma

# rss_url = "http://feeds.feedburner.com/ruanyifeng"

def rss_get_content_from_url(rss_url):
    response = get(rss_url)
    rss = RSSParser.parse(response.text)
    auther = rss.channel.title.content
    result = []
    for item in rss.channel.items:
        title = item.title.content
        link = item.link.content
        day = parser.parse(item.pub_date.content).strftime("%Y-%m-%d %H:%M:%S")
        if len(title) > 0 and len(link) > 0:
            result.append([day, title, link, auther])
    return result

def atom_get_content_from_url(rss_url):
    response = get(rss_url)
    rss = atoma.parse_atom_bytes(response.content)
    auther = rss.authors[0].name
    result = []
    for item in rss.entries:
        title = item.title.value
        link = item.id_
        day = item.published.strftime("%Y-%m-%d %H:%M:%S")
        if len(title) > 0 and len(link) > 0:
            result.append([day, title, link, auther])
    return result

# print (atom_get_content_from_url("https://blog.t9t.io/atom.xml"))

datas = open("./blogs-original.csv", 'r').read().split('\n')
urls = [x.split(",")[2] for x in datas if len(x.split(',')) >= 3]

contents = []
all_cnt = 0
skip_cnt = 0

'''
for url in urls:
    print (url)
    all_cnt += 1
    try:
        content = atom_get_content_from_url(url)
    except:
        content = rss_get_content_from_url(url)
    contents += content
'''

for url in urls:
    all_cnt += 1
    try:
        try:
            content = atom_get_content_from_url(url)
            contents += content
        except:
            content = rss_get_content_from_url(url)
            contents += content
    except:
        skip_cnt += 1
        print ("except", url)
    print ("skip rate: {:} / {:} = {:2f}%".format(skip_cnt, all_cnt, skip_cnt \
        * 100.0 / all_cnt))
    if all_cnt >= 10:
        break

contents = sorted(contents, key = lambda x: x[0], reverse = True)[: 1000]

output_file = "./../README.md"
output = open(output_file, "w")
output.write("# 中文独立博客\n")

output = open(output_file, "a")
for content in contents:
    day, title, link, auther = content
    output.write("[{title}]({link}) by {auther} on {day}\n\n".format(title \
        = title, day = day, link = link, auther = auther))

