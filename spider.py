#! /usr/bin/python

from safetyqueue import SafetyQueue
from Publisher import Publisher
from filesearch import FileFinder
import threading
from findingWriter import Writer
import time

if __name__ == '__main__':
    visited = SafetyQueue()
    unvisited = SafetyQueue()
    sharedfiles = SafetyQueue()
    threads = []

    p = Publisher(unvisited, visited)
    p.load()
    thread_p = threading.Thread(target=p.work)
    thread_p.start()

    shareFounders = []
    founder_threads = []
    for i in range(0, 5):
        finder = FileFinder(unvisited, visited, sharedfiles)
        shareFounders.append(finder)
        t = threading.Thread(target=finder.findshare)
        t.start()
        founder_threads.append(t)

    w = Writer(sharedfiles)
    w.loadFindings()
    thread_writer = threading.Thread(target=w.doWork)
    thread_writer.start()

    # wait publisher founder is finished
    thread_p.join()
    while unvisited.size() != 0:
        time.sleep(10)

    # notify found to terminate work
    for f in shareFounders:
        f.stopWork()

    for t in founder_threads:
        t.join()

    # notify writer to termniate work
    w.stopWork()
    thread_writer.join()



