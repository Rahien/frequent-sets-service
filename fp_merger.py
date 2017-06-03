import multiprocessing
import logging
from fp_functions import purge_patterns
import time
import pdb

class FPMerger(multiprocessing.Process):

    def __init__(self, name, delay, mined_queue, result_queue, workers):
        super(FPMerger, self).__init__()
        self.name = name
        self.delay = delay
        self.mined_queue = mined_queue
        self.all_mined = []
        self.workers = workers
        self.result_queue = result_queue

    def merge_mined(self):
        queue_empty = False
        
        while not queue_empty:
            try:
                mined = self.mined_queue.pop()
                if not mined:
                    # a worker gave up on life
                    self.workers -= 1
                else:
                    self.all_mined.append(mined)
            except:
                queue_empty = True

        purge_patterns(self.all_mined)
        logging.info("\n%s merging. mined: %s\n", self.name, len(self.all_mined))

    def run(self):
        print "Starting " + self.name
        
        while self.workers > 0:
            time.sleep(self.delay)
            self.merge_mined()

        self.merge_mined()
        self.result_queue.append(self.all_mined)
        print "Exiting " + self.name
