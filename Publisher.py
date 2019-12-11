#! /usr/bin/python
import requests
from safetyqueue import SafetyQueue
from log import logger
from bs4 import BeautifulSoup
from htmlparser import Parser
import time
import os

class Publisher:
    def __init__(self, unvisited, visited):
        self.unvisited = unvisited
        self.visited = visited
        self.lastSearchPage = 0
        self.parser = Parser()
        self.stoped = False

    def loadconf(self):
        if not os.path.exists('config.txt'):
            return;

        with open('config.txt', 'r') as f:
            for line in f.readlines():
                str = line.split()
                if str[0] == 'lastsearch':
                    self.lastSearchPage = int(str[1])
                    logger.info('lastSearchPage is %d'%self.lastSearchPage)

    def loadunvisited(self):
        if not os.path.exists('unvisited.txt'):
            return;

        with open('unvisited.txt','r') as f:
            for line in f.readlines():
                line = line.strip('\n')
                if line != "":
                    self.unvisited.push(line)

    def loadvisited(self):
        if not os.path.exists('visited.txt'):
            return;
        with open('visited.txt', 'r') as f:
            for line in f.readlines():
                line = line.strip('\n')
                if line != "":
                    self.visited.push(line.strip('\n'))

    def load(self):
        self.loadconf()
        self.loadvisited()
        self.loadunvisited()

    def writeconf(self):
        with open('config.txt', 'w') as f:
            f.write("%s %s"%('lastsearch', self.lastSearchPage))

    """
    From first page to get publisher
    """
    def getpublisherbyfirstpage(self, firstpage):
        None

    """
    get publisher by test a page exists
    """
    def detectpublisher(self):
        None;

    def work(self):
        startPage = self.lastSearchPage
        for i in range(startPage, 1000):
            url = "https://vdisk.weibo.com/?cid={:d}".format(i)
            self.listPublisher(url)
            self.lastSearchPage = i
            self.writeconf()
            time.sleep(3)
        logger.info("Worker for publisher search is done")
        self.stoped = True

    def listPublisher(self, url, visitedSibling=True):
        session = requests.session()
        agent = {'user-agent',
                 r'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'}
        session.headers = agent
        publishers = []
        try:
            r = session.get(url)
            if r.status_code == 200:
                shares = self.parser.getSharedItems(r.text)
                for s in shares:
                    if not self.unvisited.exist(s['uid']) and not self.visited.exist(s['uid']):
                        logger.info('find a uid %s at page %s' % (s['uid'], url))
                        if s['uid'] is not None:
                            self.unvisited.push(s['uid'])
                        else:
                            logger.warning('find a user with uid is none:%s'%(s))
                if visitedSibling:
                    siblings = self.pageList(r.text)
                    for s in siblings:
                        url = 'https://vdisk.weibo.com/' + s;
                        self.listPublisher(url, visitedSibling=False)
        except Exception as e:
            logger.info(str(e))

    def pageList(self, text):
        pages = []
        soup = BeautifulSoup(text, "html.parser")
        pagetag = soup.find(name='div', attrs={'class':'vd_page'})
        if pagetag != None:
            hrefs = pagetag.find_all(name='a')
            for href in hrefs:
                if pages.count(href.attrs['href']) == 0:
                    pages.append(href.attrs['href'])

        if len(pages) != 0:
            minlink = pages[0]
            maxlink = pages[len(pages) - 1]
            min = int((((minlink.split(sep='&'))[2]).split(sep='='))[1])
            max = int((((maxlink.split(sep='&'))[2]).split(sep='='))[1])
            pages.clear()
            for i in range(min, max + 1):
                p = minlink[0:len(minlink) - 1] + str(i)
                pages.append(p)
        return pages

    def isStopWork(self):
        return self.stoped

if __name__ == '__main__':
    unvisited = SafetyQueue()
    visited = SafetyQueue()
    p = Publisher(unvisited, visited)
    p.load()