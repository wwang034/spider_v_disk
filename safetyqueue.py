#! /usr/bin/python

from threading import Lock

class SafetyQueue:
    def __init__(self):
        self.lock = Lock()
        self.queue = []

    def push(self, element):
        self.lock.acquire()
        self.queue.append(element)
        self.lock.release()

    def pop(self):
        self.lock.acquire()
        if len(self.queue) != 0:
            e = self.queue[0]
            self.queue.remove(e)
            self.lock.release()
            return e
        self.lock.release()
        return None

    def popall(self):
        l = []
        self.lock.acquire();
        l.extend(self.queue)
        self.queue.clear()
        self.lock.release()
        return l

    def exist(self, e):
        self.lock.acquire()
        n = self.queue.count(e)
        self.lock.release()
        return n > 0

    def clone(self):
        list = []
        self.lock.acquire()
        list.extend(self.queue)
        self.lock.release()
        return list

    def size(self):
        self.lock.acquire()
        size = len(self.queue)
        self.lock.release()
        return size