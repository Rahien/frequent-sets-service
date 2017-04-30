from database import fetch_transactions, transaction_iterator, transaction_count
import pdb
import copy
import math
import logging

# frequency count for every item in a set of transactions
def item_counts(transactions):
    counts = {}
    for t in transactions:
        items = t['items']['value'].split(',')
        for item in items:
            current = counts.get(item) or 0
            counts[item] = current + 1
    return counts

# purge patterns that are contained in larger patterns
def purge_patterns(mined, hard_purge = False, priorities=None):
    sorted_mined = sorted(mined, key=lambda x: -len(x))
    max_patterns = []
    purge_count = 0
    for pattern in sorted_mined:
        purge_list = max_patterns
        if hard_purge:
            purge_list = sorted_mined
        if not contains_pattern(purge_list,pattern,priorities):
            max_patterns.append(pattern)
        else:
            purge_count += 1

    logging.info("purged %s patterns", purge_count)

    mined[:] = max_patterns

# inefficient way of tracking whether a pattern was mined before
def contains_pattern(mined,pattern, priorities=None):
    pattern_found = False
    for mined_p in mined:
        prefix_found = True
        index = -1
        for item in pattern:
            found = False
            # use that the patterns are sorted by priority
            while (index + 1) < len(mined_p):
                index += 1
                if mined_p[index] == item:
                    found = True
                    break
            if not found:
                prefix_found = False
                break;
        if prefix_found and (not pattern is mined_p):
            pattern_found = True
            if priorities:
                logging.info('pattern %s mined twice, %s had it', prioritized_pattern(pattern, priorities), prioritized_pattern(mined_p,priorities))
            break;

    return pattern_found

def prioritized_pattern(pattern,priorities):
    result = []
    for item in pattern:
        result.append((item,priorities.get(item, 0)))
    return result

class FPTree:
    depth_count = 0

    # FP tree is made up of nodes and gets build by adding transactions
    # @param transactions: iterator of transaction objects
    # @param min_support: (default 0.005) min percentage of cases an item must have
    #                     to be considered frequent
    # node = { item: "id", (redundant, but easy)
    #          children: {child-id -> node},
    #          parent: node
    #          next: node, (for linked lists)
    #          support: 1 }
    def __init__(self, options):
        if options.get('tree'):
            self.tree = options['tree']
        else:
            self.tree = {
                'root': {
                    'item': None,
                    'children': {}
                },
                'llheads': {}
            }
        self.conditional = options.get('conditional') or []

        self.transactions = options.get('transactions')
        self.min_support = options.get('min_support') or 0.005
        self.min_support_count = options.get('min_support_count')

        if options.get('priorities'):
            self.priorities = options.get('priorities')
        else:
            self.priorities = self.compute_priorities()

        if not options.get('tree'):
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
        # terrible, because side effect, but efficient because not recomputing
        self.min_support_count = math.ceil(float(basket_count)*self.min_support)

        count_tuples = sorted(counts.items(), key=lambda x: x[1])
        priorities = {}
        for i, t in enumerate(filter(lambda x: x[1] > self.min_support_count, count_tuples)[::-1]):
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
        transaction = self.process_transaction(transaction)
        target = self.tree['root']

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

    ###
    # add the given fp-tree node to the linked list for the item
    ###
    def add_to_linked_list(self, item, node):
        if not item in self.tree['llheads']:
            self.tree['llheads'][item] = node
        else:
            target = self.tree['llheads'][item]
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


    ###
    # whether or not an item is frequent in this fp tree
    ###
    def is_frequent_item(self,item):
        target = self.tree['llheads'][item]
        count = 0
        while target:
            count += target.get('support')
            target = target.get('next')

        return count >= self.min_support_count

    # mines the given fp tree non-recursively,
    # returns the trees still to be mined because of this tree 
    # and a frequent pattern if any was found
    def mine_fp(self):
        found_frequent = False

        sorted_heads = sorted(self.tree['llheads'].keys(), key=lambda x: -self.priorities[x]['index'])

        conditionals = []

        for item in sorted_heads:
            if self.is_frequent_item(item):
                found_frequent = True
                conditionals.append(self.conditional_fp_tree(item))


        frequent_pattern = self.conditional[:]
        if found_frequent: # not maximal
            frequent_pattern = None

        return conditionals, frequent_pattern

    ###
    # builds the conditional FP tree for the given item based on this tree
    ###
    def conditional_fp_tree(self, item):
        conditional = self.build_conditional_fp_tree(item)

        logging.debug("conditional tree for: %s",conditional.conditional)

        conditional.recompute_supports(item)
        conditional.remove_item(item)
        conditional.prune_infrequent()

        logging.debug("\n\n%s\n\n", conditional)

        return conditional

    ###
    # builds a new conditional fp tree for the given item bottom up from the current tree
    ###
    def build_conditional_fp_tree(self, item):
        new_tree = {
            'root': {
                'item': None,
                'children': {},
                'parent': None
            },
            'llheads': {}
        }
        condition = self.conditional[:]
        condition.append(item)

        conditional = FPTree({'tree': new_tree, 'priorities': self.priorities, 'min_support': self.min_support, 'min_support_count': self.min_support_count, 'conditional': condition })

        self.fill_conditional_tree_bottom_up(conditional, item)
        return conditional

    ###
    # fills up the given conditional fp tree by walking through the original tree
    # bottom up, using the linked list for the given item
    #
    # in this process, clones for the original nodes are remembered and then removed
    ###
    def fill_conditional_tree_bottom_up(self, conditional, item):
        leaf = self.tree['llheads'][item]
        self.tree['root']['clone'] = conditional.tree['root']

        while leaf:
            target = leaf
            while target:
                clone = target.get('clone')
                # can stop /after/ this one if we have handled this one before
                move_on = not clone
                if not clone:
                    clone = {
                        'support': target['support'],
                        'next': None,
                        'item': target['item'],
                        'children': {},
                        'parent': None
                    }
                    target['clone'] = clone
                    conditional.add_to_linked_list(clone['item'], clone)


                for item, child in target['children'].items():
                    childclone = child.get('clone', None)
                    if childclone:
                        childclone['parent'] = clone
                        clone['children'][item] = childclone

                target = target.get('parent', None)
                if not move_on:
                    target = None

            leaf = leaf.get('next', None)

        self.clean_clones()

    ###
    # removes the clones that are no longer needed. One clone war is enough.
    ###
    def clean_clones(self):
        todo = [self.tree['root']]
        while todo:
            target = todo.pop()
            target.pop('clone', None)
            todo.extend(target['children'].values())


    ###
    # recomputes the supports for the given item, starting from the nodes with that item 
    # and propagating upwards
    ###
    def recompute_supports(self, item):
        self.clear_supports(item)
        self.build_supports(item)
        self.recompute_linked_lists()

    ###
    # for building conditional fp tree
    # sets the supports to 0 for nodes except for those of the given item
    # keep the supports for the given item
    ###
    def clear_supports(self, item):
        todo = self.tree['root']['children'].values()
        # for easier termination conditions everywhere...
        self.tree['root']['support'] = 0
        while todo:
            target = todo.pop()
            if target['item'] != item:
                target['support'] = 0
            todo.extend(target['children'].values())

    ###
    # for building conditional fp tree
    # builds the supports by adding the numbers bottom up from the leaves
    ###
    def build_supports(self, item):
        leaf = self.tree['llheads'][item]
        while leaf:
            target = leaf

            while target:
                support = target.get('support')
                target = target.get('parent')
                if target:
                    target['support'] = target['support'] + support

            leaf = leaf.get('next')

    ###
    # for building conditional fp tree
    # recompute the linked lists, skip nodes that now have a support of 0
    ###
    def recompute_linked_lists(self):
        for node in self.tree['llheads'].values():
            target = node
            previous = None
            while target:
                next_node = target.get('next', None)
                if not target['support']:
                    if previous:
                        previous['next'] = next_node
                    else:
                        self.tree['llheads'][target['item']] = next_node
                else:
                    previous = target
                target = next_node

    ###
    # for building conditional fp tree
    # prunes all infrequent items in the tree
    ###
    def prune_infrequent(self):
        for item in copy.copy(self.tree['llheads']):
            if not self.is_frequent_item(item):
                self.prune_item(item)

    ###
    # for building conditional fp tree
    # prunes the given item by removing it an connecting its parent to its children if any
    # http://wimleers.com/sites/wimleers.com/files/FP-Growth%20presentation%20handouts%20%E2%80%94%C2%A0Florian%20Verhein.pdf
    # this seems an optional performance increase, so will not do it for now...
    # it seems tougher wrt ll and tree consistency (mergers!!!)
    #
    # simply removing it from the heads will do for now...
    ###
    def prune_item(self, item):
        logging.debug("pruning item %s",item)
        self.tree['llheads'].pop(item, None)

    ###
    # for building conditional fp tree
    # Removes the item from the tree
    # !! this means all nodes that are descendents of the item will be cut too !!
    ###
    def remove_item(self, item):
        logging.debug("removing item %s",item)
        node = self.tree['llheads'][item]
        while node:
            node['parent']['children'].pop(item,None)
            next = node.get('next')
            node['next'] = None
            node = next

        self.tree['llheads'].pop(item, None)

    # making the string representation of the tree a little more friendly
    def __str__(self):
        next_level = self.tree['root']['children'].values()
        result_string = ["fp-tree, min-support:", str(self.min_support_count), "\nnodes:\n"]

        while next_level:
            current_level = sorted(next_level, key=lambda x: x['support'])
            next_level = []
            while current_level:
                target = current_level.pop()
                result_string.extend(["{",target['item']," sup:",str(target['support'])," size:",str(len(target['children']))," parent:", (target['parent']['item'] or "None"),"}"])
                next_level.extend(target['children'].values())

            result_string.append("\n\n")

        result_string.append("linked-list:\n")
        for key, target in self.tree['llheads'].items():
            result_string.extend([key, " -> ", "{",target['item']," sup:",str(target['support'])," size:",str(len(target['children']))," parent:", (target['parent']['item'] or "None"),"}\n"])

        return ''.join(result_string)

