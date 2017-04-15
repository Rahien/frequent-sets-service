import flask
import json
import math
from database import fetch_transactions, transaction_iterator, transaction_count
from fp_functions import item_priority, FPTree

@app.route("/version")
def version():
    return "frequent-items v.0.0.1"

@app.route("/transactions")
def transactions():
    return flask.jsonify(fetch_transactions('skills'))

@app.route("/count-transactions")
def count_transactions():
    count = 0
    for t in transaction_iterator('skills'):
        count +=1
    return "found {0} transactions".format(count)

@app.route("/build-fp")
def build_fp():
    priorities = get_priorities()
    fp = FPTree(priorities)

    for t in transaction_iterator('skills'):
        fp.add_transaction(t)

    print('all done')
    data_as_str = json.dumps(fp.root)
    return flask.Response(response=data_as_str, status=200, mimetype="application/json")                    

@app.route("/count-items")
def count_items():
    priorities = get_priorities()
    return flask.jsonify(priorities)

def get_priorities():
    baskets = transaction_count('skills')
    transactions = transaction_iterator('skills')
    return item_priority(transactions, math.ceil(0.005 * float(baskets)))
