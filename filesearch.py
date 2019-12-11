#! /usr/bin/python

import os
from safetyqueue import SafetyQueue
import xlrd
import xlwt
from sharefile import ShareFile
import requests
import json
from bs4 import BeautifulSoup
from log import logger
from htmlparser import Parser
import time


class FileFinder:
    count=0
    def __init__(self, unvisited, visited, shares):
        self.unvisited = unvisited
        self.visited = visited
        self.shares = shares
        self.session = requests.session()
        self.parser = Parser()
        agent = {'user-agent',
                 r'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        self.session.headers = agent
        self.stop = False

    def findshare(self):
        while not self.stop and self.unvisited.size() != 0:
            publisher = self.unvisited.pop()
            if publisher == None:
                time.sleep(2)
                continue

            #construct a new session
            self.session = requests.session()
            agent = {'user-agent',
                     r'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
            self.session.headers = agent

            self.findShareFromPublisher(publisher)
            self.visited.push(publisher)
            FileFinder.count += 1
            if FileFinder.count >= 5:
                self.writepublishback()
                FileFinder.count = 0

            time.sleep(3)
    
        
        self.writepublishback()

    def stopWork(self):
        self.stop = True

    def findShareFromPublisher(self, p):
        url = r'https://vdisk.weibo.com/u/' + p;
        self.findShareFromUrl(url)

    def findShareFromUrl(self, url, travseSibling = True):
        try:
            r = self.session.get(url)
            if r.status_code == 200:
                self.listFile(r.text, url)
                # travser other pages
                if travseSibling == True:
                    soup = BeautifulSoup(r.text, "html.parser")
                    nextPages = self.pageList(soup)
                    if len(nextPages) > 0:
                        for p in nextPages:
                            logger.info('To find share in page %s' % (url + p))
                            self.findShareFromUrl(url + p, travseSibling = False) #no need to traverse sibling
        except Exception as e:
            logger.warning("Unexpected error: %s"%str(e))

    def writepublishback(self):
        v = self.visited.clone()
        u = self.unvisited.clone()
        with open('visited.txt', 'w') as f:
            for s in v:
                f.write(s+'\n')

        with open('unvisited.txt', 'w') as f:
            for s in u:
                f.write(s+'\n')

    def listFile(self, text, url):
        items = self.parser.getSharedItems(text)
        for item in items:
            if not item['is_dir']:
                bytes = 'unknown'
                if 'bytes' in item:
                    bytes = item['bytes']
                sina_uid = 'unknown'
                if 'sina_uid' in item:
                    sina_uid = item['sina_uid']
                elif 'uid' in item:
                    sina_uid = item['uid']
                sf = ShareFile(item['filename'], bytes, item['url'], sina_uid)
                self.shares.push(sf)
            else:
                self.searchInDirectory(item['url'])

    def pageList(self, soup):
        vd_page = soup.find(name='div', attrs={'class': 'vd_page'})
        pages = []
        if vd_page != None:
            page_links = vd_page.find_all(name='a')
            for p in page_links:
                if pages.count(p.attrs['href']) == 0: # ignore the next page by button
                    pages.append(p.attrs['href'])

        #link page is not continuous, construct link page in continuous way
        if len(pages) != 0:
            min = int(pages[0].split(sep='=')[1])
            max = int(pages[len(pages)-1].split(sep='=')[1])
            pages.clear()
            for i in range(min, max+1):
                pages.append('?page=%d'%i)

        logger.info('pages is %s' % pages)
        return pages

    def searchInDirectory(self, dir_url, travserSibling = True):
        try:
            r = self.session.get(dir_url)
            if r.status_code == 200:
                self.listFile(r.text, dir_url)
                if (travserSibling):
                    pages = self.pageListInDirectory(r.text, dir_url)
                    for p in pages:
                        self.searchInDirectory(dir_url+p, travserSibling = False)
        except Exception as e:
            logger.warning("Unexpected error: %s"%str(e))

    def pageListInDirectory(self, text, dir_url):
        soup = BeautifulSoup(text, "html.parser")
        vd_page = soup.find(name='div', attrs={'class': 'vd_page'})
        pages = []
        if vd_page != None:
            page_links = vd_page.find_all(name='a')
            for p in page_links:
                if pages.count(p.attrs['href']) == 0:  # ignore the next page by button
                    pages.append(p.attrs['href'])

        if len(pages)  != 0:
            minlink = pages[0]
            maxlink = pages[len(pages)-1]
            min = int((((minlink.split(sep='&'))[2]).split(sep='='))[1])
            max = int((((maxlink.split(sep='&'))[2]).split(sep='='))[1])
            pages.clear()
            for i in range(min, max+1):
                p = minlink[0:len(minlink)-1] + str(i)
                pages.append(p)
            logger.info("page in directory: %s"%pages)
        return pages

    def convertJsonItem(self, tag):
        downloadtag = tag.find(name='a', attrs={'class':'vd_pic_v2 vd_dload'})
        share_item = json.loads(downloadtag.attrs['data-info'])
        share_item['url'] = self.stripSlash(share_item['url'])
        return share_item

    def stripSlash(self, str):
        s = ''
        for c in str:
            if c != r'\\':
                s += c
        return s

if __name__ == '__main__':
    visited = SafetyQueue()
    unvisited = SafetyQueue()
    shares = SafetyQueue()
    founder = FileFinder(visited, unvisited, shares)
    '''
    with open('vdisk.html', encoding='UTF-8') as f:
        s = f.read()
        founder.listFile(s)
    '''
    url = r'https://vdisk.weibo.com/u/5698929130'
    founder.findShareFromUrl(url)


    #founder.findShare('5811552055')
    '''
    for i in range(1, 100):
        shares.push(ShareFile(str(i), str(i)))

    founder = FileFinder(visited, unvisited, shares)
    founder.writeFindingToExcel()

    for i in range(100, 200):
        shares.push(ShareFile(str(i), str(i)))
    founder.writeFindingToExcel()
    '''

