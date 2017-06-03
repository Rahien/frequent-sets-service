import multiprocessing
import logging
import time
from fp_functions import contains_pattern, purge_patterns

class FPWorker(multiprocessing.Process):

    def __init__(self, main_queue, mined_queue, max_prio):
        super(FPWorker, self).__init__()
        self.main_queue = main_queue
        self.queue = []
        self.mined_queue = mined_queue
        self.max_prio = max_prio

    def run(self):
        print "Starting " + self.name
        
        todo = self.next()
        while todo:
            self.mine_tree(todo)
            todo = self.next()
                
        # notify suicide
        self.mined_queue.append(None)
        print "Exiting " + self.name

    def next(self, lives = 3):
        result = None
        try:
            result = self.queue.pop()
        except:
            try:
                result = self.main_queue.pop()
            except:
                result = None

        if not result and lives > 0:
            time.sleep(10) # maybe someone will put stuff on soon...
            result = self.next(lives-1)

        return result

    def add_to_queue(self, conditionals):
        max_in_own = 10
        if conditionals:
            to_take = max(0,max_in_own - len(self.queue))
            self.queue.extend(conditionals[:to_take])

            for conditional in conditionals[to_take:]:
                self.main_queue.append(conditional)
        logging.info("own: {}, main: {}".format(len(self.queue), len(self.main_queue)))
            
    def mine_tree(self,tree):
        conditionals, pattern = tree.mine_fp()

        first_conditional = next(iter(tree.conditional or []), None)
        depth = len(tree.conditional)

        if pattern:
            self.mined_queue.append(pattern)

        self.add_to_queue(conditionals)

        logging.info("\nt: %s -- first-prio: %s/%s,depth: %s,heads: %s, queue: %s\n",
                     self.name,
                     tree.priorities.get(first_conditional,{}).get('index', 0), self.max_prio,
                     depth, len(tree.tree['llheads']), len(self.queue))
