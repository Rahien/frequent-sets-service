import flask
import json
from database import fetch_transactions, transaction_iterator, transaction_count
from fp_functions import FPTree, purge_patterns
from fp_worker import FPWorker
from fp_cleaner import FPCleaner
import threading
import thread
import sys
import os
import helpers

sys.setrecursionlimit(3000)

processes = {}

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
        'min_support':float(flask.request.args.get('support', '0.005'))
    })
    return flask.Response(response=str(fp), status=200, mimetype="text/plain")

@app.route("/mining-state/<id>")
def mining_state(id):
    process = processes.get(id, None)
    if not process:
        flask.abort(404)

    result = process.get('result', None)

    if not result:
        res = json.dumps({"queue":len(process.get('queue', [])), 
                          "mined": len(process.get('mined', [])) })
        return flask.Response(response=res, status=202, mimetype="application/json")
    else:
        res = json.dumps(result)
        processes.pop(id, None)
        return flask.Response(response = res, status=200, mimetype="application/json")

@app.route("/mine-fp/<config>")
def mine_tree(config):
    id = helpers.generate_uuid()
    process = {'id': id}
    processes[id] = process
    support = float(flask.request.args.get('support', '0.005'))

    thread.start_new_thread(do_threaded_mining, (config, support, process))

    return flask.Response(response = json.dumps(process) , status=202, mimetype="application/json")

def do_threaded_mining(config, support, process):
    fp = FPTree({
        'transactions':transaction_iterator(config),
        'min_support': support
    })
    mined = []
    queue = []
    process['mined'] = mined
    process['queue'] = queue
    lock = threading.Lock()
    workers = []

    max_prio = sorted(fp.tree['llheads'].keys(), key=lambda x: -fp.priorities[x]['index'])
    if max_prio:
        max_prio = fp.priorities.get(max_prio[0])['index']
    else:
        max_prio = 0

    # first fill up queue
    conditionals, unused_frequent_pattern = fp.mine_fp()
    queue.extend(conditionals)
    threads = int(os.environ.get('FP_WORKERS'))
    for number in range(1,threads):
        worker = FPWorker(number, queue,max_prio, mined, lock)
        workers.append(worker)
        worker.start()

    cleaner = FPCleaner("cleaner", 6,queue, mined, lock)
    cleaner.start()

    for worker in workers:
        worker.join()

    cleaner.join()

    purge_patterns(mined, hard_purge=True)
    
    process['result'] = mined

