import threading
import logging
from fp_functions import purge_patterns
import time

class FPCleaner(threading.Thread):

    def __init__(self, name, delay, queue, mined, lock):
        threading.Thread.__init__(self)
        self.name = name
        self.delay = delay
        self.queue = queue
        self.mined = mined
        self.lock = lock

    def run(self):
        print "Starting " + self.name

        while self.queue:
            self.lock.acquire()
            logging.info("\n%s cleaning\n", self.name)
            purge_patterns(self.mined)
            self.lock.release()
            time.sleep(20)

        print "Exiting " + self.name
