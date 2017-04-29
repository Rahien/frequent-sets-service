import flask
import json
from database import fetch_transactions, transaction_iterator, transaction_count
from fp_functions import FPTree
import sys

sys.setrecursionlimit(3000)

@app.route("/version")
def version():
    return "frequent-items v.0.0.1"

@app.route("/transactions/<config>")
def transactions(config):
    return flask.jsonify(fetch_transactions(config))

@app.route("/build-fp/<config>")
def build_tree(config):
    fp = FPTree({
        'transactions':transaction_iterator(config),
        'min_support':float(flask.request.args.get('support', '0.005'))
    })
    data_as_str = json.dumps(map((lambda x: x['item'] + " sup:" + str(x['support']) + " size:" + str(len(x['children']))), fp.tree['root']['children'].values()))
    return flask.Response(response=data_as_str, status=200, mimetype="application/json")                    

@app.route("/show-fp/<config>")
def show_tree(config):
    fp = FPTree({
        'transactions':transaction_iterator(config),
        'min_support':float(flask.request.args.get('support', '0.005')),
        'maximal_only':bool(flask.request.args.get('maxonly',True))
    })
    return flask.Response(response=str(fp), status=200, mimetype="text/plain")

@app.route("/mine-fp/<config>")
def mine_tree(config):
    fp = FPTree({
        'transactions':transaction_iterator(config),
        'min_support':float(flask.request.args.get('support', '0.005')),
        'maximal_only':bool(flask.request.args.get('maxonly',True))
    })
    mined = []
    max_patterns = fp.mine_fp(mined)
    return flask.Response(response=str(max_patterns), status=200, mimetype="text/plain")
