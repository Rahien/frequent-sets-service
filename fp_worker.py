import threading
import logging
from fp_functions import contains_pattern

class FPWorker(threading.Thread):

    def __init__(self, name, queue, max_prio, mined, lock):
        threading.Thread.__init__(self)
        self.name = name
        self.queue = queue
        self.mined = mined
        self.lock = lock
        self.max_prio = max_prio

    def run(self):
        print "Starting " + self.name

        todo = self.next()
        while todo:
            self.mine_tree(todo)
            todo = self.next()

        print "Exiting " + self.name

    def next(self):
        result = None
        self.lock.acquire()
        if self.queue:
            result = self.queue.pop()
        self.lock.release()
        return result

    def mine_tree(self,tree):
        conditionals, pattern = tree.mine_fp_threaded()

        first_conditional = next(iter(tree.conditional or []), None)
        depth = len(tree.conditional)

        if pattern:
            self.lock.acquire()
            if not contains_pattern(self.mined, pattern):
                self.mined.append(pattern)
            self.lock.release()

        if conditionals:
            self.lock.acquire()
            self.queue.extend(conditionals)
            self.lock.release()

        logging.info("\nt: %s -- first-prio: %s/%s,depth: %s,heads: %s, mined: %s\n, queue: %s\n",
                     self.name,
                     tree.priorities.get(first_conditional,{}).get('index', 0), self.max_prio,
                     depth, len(tree.tree['llheads']), len(self.mined), len(self.queue))
