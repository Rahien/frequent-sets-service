import pdb
# frequency count for every item in a set of transactions
def item_counts(transactions):
    counts = {}
    for t in transactions:
        items = t['items']['value'].split(',')
        for item in items:
            current = counts.get(item) or 0
            counts[item] = current + 1
    return counts

def item_priority(transactions, min_support_count=0):
    counts = item_counts(transactions)
    count_tuples = sorted(counts.items(), key=lambda x: x[1])
    priorities = {}
    for i, t in enumerate(filter(lambda x: x[1] > min_support_count, count_tuples)[::-1]):
        priorities[t[0]]= { 'index': i, 'support': t[1] }
    return priorities

    
class FPTree:
    # node = { item: "id", (redundant, but easy)
    #          children: {child-id -> node},
    #          next: node,
    #          support: 1 }
    def __init__(self, priorities):
        self.root = {
            'item': None,
            'children': {}
        }
        self.llheads = {}
        self.priorities = priorities

    def add_transaction(self, transaction):
        print("receiving transaction")
        transaction = self.sorted_transaction(transaction)
        target = self.root

        print("adding transaction")
        while len(transaction) > 0:
            head = transaction.pop(0)

            if not head in target['children']:
                node = {
                    'support': 0,
                    'next': None,
                    'item': head,
                    'children': {}
                }
                target['children'][head] = node
                self.add_to_linked_list(head, node)

            target = target['children'][head]
            target['support'] += 1

        print("transaction done")

    def add_to_linked_list(self, item, node):
        if not item in self.llheads:
            self.llheads[item] = node
        else:
            target = self.llheads[item]
            while target.get('next', None):
                target = target['next']
            target['next'] = node
        
    # receives a transaction and returns it as
    # a sorted list of frequent items
    def sorted_transaction(self, transaction):
        return sorted(filter(lambda x: x in self.priorities, transaction['items']['value'].split(',')), key=lambda x: self.priorities[x]['index'])






