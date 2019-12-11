#! /usr/bin/python
import json
from bs4 import BeautifulSoup

class Parser:
    def getSharedItems(self, text):
        items = []
        soup = BeautifulSoup(text, "html.parser")
        share_table = soup.find(name='table', attrs={'class': 'v_sort v_sort_body'})
        if share_table == None:  # some page not exist share item
            return items

        trTags = share_table.find_all(name='tr')
        for tag in trTags:
            share_item = self.convertJsonItem(tag)
            # share_item is like this below
            # {'copy_ref': 'ruz3wniZH8uMN', 'filename': '多元智能理论的科学性（加德纳答沃德豪斯女士的批评）.pdf', 'uid': '5698929130', 'link': 'http://vdisk.weibo.com/s/ruz3wniZH8uMN', 'is_dir': False, 'count_browse': '82', 'url': 'http://vdisk.weibo.com/s/ruz3wniZH8uMN', 'sina_uid': '5698929130'}
            items.append(share_item)
        return items


    def convertJsonItem(self, tag):
        downloadtag = tag.find(name='a', attrs={'class':'vd_pic_v2 vd_dload'})
        share_item = json.loads(downloadtag.attrs['data-info'])
        if 'link' in share_item: #some time url is represented by link
            share_item['url'] = share_item['link']
        share_item['url'] = self.stripSlash(share_item['url'])
        if 'sina_uid' in share_item:
            share_item['uid'] = share_item['sina_uid']
        return share_item

    def stripSlash(self, str):
        s = ''
        for c in str:
            if c != r'\\':
                s += c
        return s