#! /usr/bin/python
import os
from log import logger
import xlrd
import xlwt
from sharefile import ShareFile
import time
import threading
from safetyqueue import SafetyQueue

fileGroup = {".pdf":"pdf file",
             ".txt":"text file",
             ".zip":'compress file',
             ".7z":'compress file',
             ".rar":'compress file',
             ".xls":'excel file',
             ".xlsx":'excel file',
             '.xlsm':'excel file',
             ".jpg":'image file',
             ".png":'image file',
             '.jpeg':'image file',
             '.heic':'image file',
             '.mov':'image file',
             '.mp3':'music file',
             '.mp4':'music file',
             '.doc':'document file',
             '.docx':'document file',
             '.ppt':'power point file',
             '.pptx':'power point file',
             '.exe':'executable file'}

class Writer:
    def __init__(self, shares):
        self.shares = shares
        self.stop = False
        self.findings = {} # a dictionary for finding. key is file type, such as image file. value is also a dictionary.
        self.count = {}

    '''
    Load all share items in excel file
    '''
    def loadFindings(self):
        groups = []
        for (k, v) in fileGroup.items():
            if groups.count(v) == 0:
                groups.append(v)
                self.findings[v] = {}
                self.count[v] = 0

        # for others file
        self.findings['others'] = {}
        self.count['others'] = 0
        groups.append('others')

        for type in groups:
            xlsx = type + '.xls'
            if os.path.exists(xlsx):
                wb = xlrd.open_workbook(xlsx)
                sheet = wb.sheets()[0]
                for i in range(0, sheet.nrows):
                    values = sheet.row_values(i)
                    name = str(values[0])
                    size = str(values[1])
                    url = str(values[2])
                    sina_uid = str(values[3])
                    if type == 'image file':  # for image file, check url is same
                        self.findings[type][url] = ShareFile(name, size, url, sina_uid)
                    else:
                        self.findings[type][name] = ShareFile(name, size, url, sina_uid)
                self.count[type] = len(self.findings[type])


    def doWork(self):
        while not self.stop:
            if self.shares.size() > 1000:
                self.writeFindingToExcel()
            time.sleep(10)

        self.writeFindingToExcel(lastBatch = True)
        logger.info('quit the xml writer now')

    def stopWork(self):
        self.stop = True

    def groupShares(self, shares):
        group = {}
        for s in shares:
            gName = self.groupName(s.name)
            if not (gName in group):
                group[gName] = []
            group[gName].append(s)
        return group

    def groupName(self, name):
        dotIndex = name.rfind('.')
        if dotIndex == -1:
            return 'others'
        else:
            ext = name[dotIndex:].lower()
            if ext in fileGroup:
                return fileGroup[ext]
            else:
                return 'others'

    def writeFindings(self, group, lastBatch = False):
        for (k, v) in group.items():
            for s in v:
                if k == 'image file':
                    if s.url not in self.findings[k]:
                        self.findings[k][s.url] = s
                else:
                    if s.name not in self.findings[k]:
                        self.findings[k][s.name] = s

            newCount = len(self.findings[k])
            logger.info('find %d for %s'%(newCount, k))
            if lastBatch or newCount - self.count[k] > 100: # every find 100 items, write to excel
                wb = xlwt.Workbook()
                ws = wb.add_sheet(k)
                i = 0
                for v_k in self.findings[k].keys():
                    v = self.findings[k][v_k]
                    ws.write(i, 0, v.name)
                    ws.write(i, 1, v.size)
                    ws.write(i, 2, v.url)
                    ws.write(i, 3, v.sina_uid)
                    formular = 'HYPERLINK("%s";"link")' % (v.url)
                    ws.write(i, 4, xlwt.Formula(formular))
                    i = i + 1

                xlsx = k + '.xls'
                wb.save(xlsx)
                self.count[k] = newCount
                logger.info('save total %d into %s' % (newCount, xlsx))

    def writeFindingToExcel(self, lastBatch = False):
        findings = self.shares.popall()
        group = self.groupShares(findings)
        self.writeFindings(group, lastBatch)

if __name__ == '__main__':
    q = SafetyQueue()
    w = Writer(q)
    t = threading.Thread(target=w.doWork)
    t.start()
    time.sleep(20)
    w.stopWork()
    t.join()
'''
        existed.extend(l)

        for i in range(0, len(existed)):
            ws.write(i, 0, existed[i].name)
            ws.write(i, 1, existed[i].url)
            formular = 'HYPERLINK("%s";"link")'%(existed[i].url)
            ws.write(i, 2, xlwt.Formula(formular))
        wb.save(xlsx)
        logger.info('save total %d into excel file %s'%(len(existed), xlsx))
'''