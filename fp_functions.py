from database import fetch_transactions, transaction_iterator, transaction_count
import pdb
import math

# frequency count for every item in a set of transactions
def item_counts(transactions):
    counts = {}
    for t in transactions:
        items = t['items']['value'].split(',')
        for item in items:
            current = counts.get(item) or 0
            counts[item] = current + 1
    return counts

class FPTree:
    # FP tree is made up of nodes and gets build by adding transactions
    # @param transactions: iterator of transaction objects
    # @param min_support: (default 0.005) min percentage of cases an item must have
    #                     to be considered frequent
    # node = { item: "id", (redundant, but easy)
    #          children: {child-id -> node},
    #          parent: node
    #          next: node, (for linked lists)
    #          support: 1 }
    def __init__(self, transactions,min_support=0.005):
        self.root = {
            'item': None,
            'children': {}
        }
        self.llheads = {}
        self.transactions = transactions
        self.min_support = min_support
        self.priorities = self.compute_priorities()
        self.build_fp_tree()

    ###
    # build the fp_tree by looping over all transactions and adding the transactions
    # to the tree one by one
    ###
    def build_fp_tree(self):
        self.transactions.reset();
        for t in self.transactions:
            self.add_transaction(t)

    ###
    # compute the item priorities (support) based on the transactions and the min_support
    # this means looping over the transactions once and counting support for all items
    # items with a support lower than the min_support will be kicked out
    ###
    def compute_priorities(self):
        counts = item_counts(self.transactions)
        basket_count = self.transactions.counted()

        min_support_count = math.ceil(float(basket_count)*self.min_support)

        count_tuples = sorted(counts.items(), key=lambda x: x[1])
        priorities = {}
        for i, t in enumerate(filter(lambda x: x[1] > min_support_count, count_tuples)[::-1]):
            priorities[t[0]]= { 'index': i, 'support': t[1] }

        return priorities

    ###
    # adds the transaction to the fp-tree.
    #
    # 1) process the transaction to filter out non-frequent items and sort it according priority
    # 2) starting from the root of the tree,
    #    in order of the transaction, for each item
    #    2.1) if the item is in the children of the current node,
    #            increase the support for the child
    #    2.2) else
    #            create a new child node and set the spport to 1
    #            add this new node to the linked list for that item
    ###
    def add_transaction(self, transaction):
        print("receiving transaction")
        transaction = self.process_transaction(transaction)
        target = self.root

        print("adding transaction")
        while len(transaction) > 0:
            head = transaction.pop(0)

            if not head in target['children']:
                node = {
                    'support': 0,
                    'next': None,
                    'item': head,
                    'children': {},
                    'parent': target
                }
                target['children'][head] = node
                self.add_to_linked_list(head, node)

            target = target['children'][head]
            target['support'] += 1

        print("transaction done")

    ###
    # add the given fp-tree node to the linked list for the item
    ###
    def add_to_linked_list(self, item, node):
        if not item in self.llheads:
            self.llheads[item] = node
        else:
            target = self.llheads[item]
            while target.get('next', None):
                target = target['next']
            target['next'] = node
        
    ###
    # receives a transaction, sorts it according to the tree's priorities.
    # also removes infrequent items
    #
    # returns a list of items, representing the processed transaction
    ###
    def process_transaction(self, transaction):
        return sorted(filter(lambda x: x in self.priorities, transaction['items']['value'].split(',')), key=lambda x: self.priorities[x]['index'])






