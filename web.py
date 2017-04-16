import flask
import json
from database import fetch_transactions, transaction_iterator, transaction_count
from fp_functions import FPTree

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
def build_tree():
    fp = FPTree(transaction_iterator('skills'))
    print('all done')
    data_as_str = json.dumps(map((lambda x: x['item'] + " sup:" + str(x['support']) + " size:" + str(len(x['children']))), fp.root['children'].values()))
    return flask.Response(response=data_as_str, status=200, mimetype="application/json")                    
