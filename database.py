import helpers
import yaml

def transaction_iterator(config):
    return TransactionWalker(config,1000)

def fetch_transactions(config, limit=10000, offset=0):
    query = transaction_query(config)
    query += " ORDER BY ?basket LIMIT {0} OFFSET {1}".format(limit, offset)
    return helpers.query(query).get('results',{}).get('bindings',[])

def transaction_count(config):
    query = "SELECT (COUNT (DISTINCT (?basket))) AS ?count WHERE {{ {0} }}".format(transaction_query(config))
    result = helpers.query(query)
    return result['results']['bindings'][0]['count']['value']

def transaction_query(config):
    with open('/app/config.yaml', 'r') as stream:
        config_file = yaml.load(stream)
        return config_file[config]['transactions']

class TransactionWalker:
    def __init__(self, config, limit=1000):
        self.config = config
        self.limit = limit
        self.reset()

    def __iter__(self):
        return self

    def __next__(self):
        if self.has_more():
            result = self.batch[self.batch_current]
            self.batch_current += 1
            return result
        else:
            raise StopIteration

    def next(self):
        return self.__next__()

    def reset(self):
        self.offset = 0
        self.batch_current = 0
        self.batch = None

    def counted(self):
        return self.batch_current + self.offset

    def has_more(self):
        # fetch batch first time
        if self.batch is None:
            self.batch = fetch_transactions(self.config, self.limit, self.offset)
        # fetch new batch
        if self.batch_current >= self.limit:
            self.offset = self.offset + self.limit
            self.batch = fetch_transactions(self.config, self.limit, self.offset)
            self.batch_current = 0

        return self.batch_current < len(self.batch)


        
        
