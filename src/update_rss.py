#!/usr/bin/python
# -*- coding: utf-8 -*-

from rss_parser import RSSParser
import requests
from dateutil import parser
from datetime import datetime
from urllib.parse import urlparse
import re
import atoma

# rss_url = "http://feeds.feedburner.com/ruanyifeng"

def if_contain_symbol(keyword):
    symbols = "~@#$^&\\ä»æçæ³å°ç"
    for symbol in symbols:
        if symbol in keyword:
            return True
    return False


def rss_get_content_from_url(rss_url):
    response = requests.get(rss_url, timeout = 1)
    rss = RSSParser.parse(response.text)
    open('valid_rss.txt', "a").write(rss_url + "\n")
    auther = rss.channel.title.content
    result = []
    index = 0
    for item in rss.channel.items:
        title = item.title.content
        link = item.link.content
        day = parser.parse(item.pub_date.content).strftime("%Y-%m-%d %H:%M:%S")
        result.append([day, title, link, auther])
        index += 1
        if index >= 100: break
    return result

def atom_get_content_from_url(rss_url):
    response = requests.get(rss_url, timeout = 1)
    rss = atoma.parse_atom_bytes(response.content)
    open('valid_rss.txt', "a").write(rss_url + '\n')
    auther = rss.authors[0].name
    result = []
    index = 0
    for item in rss.entries:
        title = item.title.value
        link = item.id_
        day = item.published.strftime("%Y-%m-%d %H:%M:%S")
        result.append([day, title, link, auther])
        index += 1
        if index >= 100: break
    return result

def get_urls_from_independent_blogs():
    print ('1. get_urls_from_independent_blogs begin')
    datas = requests.get('https://raw.githubusercontent.com/timqian/chinese-independent-blogs/master/blogs-original.csv').text.split('\n')[1: ]
    urls = [x.split(",")[2].strip(' ') for x in datas if len(x.split(',')) >= 3]
    print ('1. get_urls_from_independent_blogs done len = ', len(urls))
    print ('-' * 50 + '\n\n')
    return urls

def get_urls_from_valid_blog():
    output_urls = []
    rss_urls = open('valid_rss.txt', 'r').read().split('\n')
    rss_urls = list(set(rss_urls))
    print ('2. get_urls_from_valid_blog begin input_len = ', len(rss_urls))
    index = 0
    domains = []
    for url in rss_urls:
        if len(url) < 2: continue
        info = urlparse(url.strip(' '))
        main_page = info.scheme + "://" + info.netloc
        # print ('main_page: ', main_page)
        link_suffixs = ['friends', 'link', 'links.html']
        link_list = []
        for suffix in link_suffixs:
            try:
                link_page = main_page + '/' + suffix
                # print ('link_page', link_page)
                res = requests.get(link_page, timeout = 1)
                link_list = re.findall(r"(?<=href=\").+?(?=\")|(?<=href=\').+?(?=\')", res.text)
                link_list = [x for x in link_list if main_page not in x]
                # print ('link_list', link_list)
                output_urls += link_list
            except:
                pass
        index += 1
        print ('get_urls_from_valid_blog process:{:}/{:}={:.2f}, output = {:}'.format(index, len(rss_urls), index / len(rss_urls), len(output_urls)))
    output_urls = list(set(output_urls))
    print ('2. get_urls_from_valid_blog done, output_len = {:}'.format(len(output_urls)))
    print ('-' * 50 + '\n\n')
    return output_urls

def get_blogs_from_rss(rss_urls, limit = 2):
    contents = []
    all_cnt = 0
    skip_cnt = 0
    print ('3. get_blogs_from_rss begin input_len = ', len(rss_urls))
    for url in rss_urls:
        print ("url: ", url)
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
            print ("except")
        print ("skip rate: {:} / {:} = {:2f}%".format(skip_cnt, all_cnt, skip_cnt * 100.0 / all_cnt))
        print ("process: {:} / {:} = {:2f}%".format(all_cnt, len(rss_urls), all_cnt / len(rss_urls)))
        if all_cnt >= limit:
            break
    print ('3. get_blogs_from_rss done, output_len = {:}'.format(len(contents)))
    print ('-' * 50 + '\n\n')
    return contents

def get_blogs_from_link_urls(link_urls, limit = 2):
    contents = []
    all_cnt = 0
    skip_cnt = 0
    
    rss_suffix = ['feed.xml', 'atom.xml', 'feed', 'index.xml', 'rss.xml', 'rss']
    print ('4. get_blogs_from_link_url input_len = ', len(link_urls))
    for url in link_urls:
        print ("url: ", url)
        all_cnt += 1
        fail = 1
        for suf in rss_suffix:
            rss = url + '/' + suf
            try:
                try:
                    content = atom_get_content_from_url(url)
                    contents += content
                    fail = 0
                except:
                    content = rss_get_content_from_url(url)
                    contents += content
                    fail = 0
                break
            except:
                pass
        if fail == 1:
            print ('except')
        skip_cnt += fail
        print ("skip rate: {:} / {:} = {:2f}%".format(skip_cnt, all_cnt, skip_cnt * 100.0 / all_cnt))
        print ("process: {:} / {:} = {:2f}%".format(all_cnt, len(link_urls), all_cnt / len(link_urls)))
        if all_cnt >= limit:
            break
    # print ('link_urls content', contents)
    print ('4. get_blogs_from_link_url done, output_len = {:}'.format(len(contents)))
    print ('-' * 50 + '\n\n')
    return contents


def write_output(contents, output_file):
    print ('5. write_output input_len = ', len(contents))
    index = 0
    contents = sorted(contents, key = lambda x: x[0], reverse = True)[: 1000]
    output = open(output_file, "w")
    output.write("# 中文独立博客\n")
    
    last_day = ""
    output = open(output_file, "a")
    for content in contents:
        day, title, link, auther = content
        now_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if len(title) > 0 and len(link) > 3 and "<![" not in title and if_contain_symbol(title) == False and day < now_ts:
            today = day.split(" ")[0]
            if today != last_day:
                output.write("\n### {}\n".format(today))
                last_day = today
            output.write("[{title}]({link})  by  {auther}  at  {day}\n\n".format(title \
                = title, day = day, link = link, auther = auther))
    print ('5. write_output done')
    print ('-' * 50 + '\n\n')

if __name__ == "__main__":
    is_test = 1
    if is_test == 1:
        limit = 5
        output = './test'
    else:
        limit = 100000
        output = "./../index.md"
    rss_urls = get_urls_from_independent_blogs()
    invite_urls = get_urls_from_valid_blog()
    open('valid_rss.txt', "w").write('')
    contents = get_blogs_from_rss(rss_urls, limit) + get_blogs_from_link_urls(invite_urls, limit)
    write_output(contents, output)
