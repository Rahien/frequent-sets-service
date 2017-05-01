import flask
import json
from database import fetch_transactions, transaction_iterator, transaction_count
from fp_functions import FPTree, purge_patterns
from fp_worker import FPWorker
from fp_merger import FPMerger
import thread
import sys
import os
import helpers
import pdb
from multiprocessing import Queue

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
        workers_alive = 0
        for worker in process.get('workers'):
            if worker.is_alive():
                workers_alive += 1
        
        res = json.dumps({
            "queue":process.get('queue').qsize(), 
            "mined": process.get('mined').qsize(),
            "workers": workers_alive
        })
        return flask.Response(response=res, status=202, mimetype="application/json")
    else:
        res = json.dumps(result)
        processes.pop(id, None)
        return flask.Response(response = res, status=200, mimetype="application/json")

@app.route("/minings")
def get_minings():
    return flask.Response(response = json.dumps(processes.keys()), status = 200, mimetype="application/json")

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

    max_prio = sorted(fp.tree['llheads'].keys(), key=lambda x: -fp.priorities[x]['index'])
    if max_prio:
        max_prio = fp.priorities.get(max_prio[0])['index']
    else:
        max_prio = 0

    # first fill up queue
    main_queue = Queue()
    mined_queue = Queue()

    process['mined'] = mined_queue
    process['queue'] = main_queue
    workers = []
    process['workers'] = workers

    conditionals, unused_frequent_pattern = fp.mine_fp()
    for conditional in conditionals:
        main_queue.put(conditional)

    worker_count = int(os.environ.get('FP_WORKERS'))

    for number in range(0,worker_count):
        worker = FPWorker(main_queue, mined_queue, max_prio)
        workers.append(worker)
        worker.start()

    result_queue = Queue()
    merger = FPMerger("merger", 60, mined_queue, result_queue, worker_count)
    merger.start()

    for worker in workers:
        worker.join()

    merger.join()

    result = result_queue.get()
    purge_patterns(result, hard_purge=True)
        
    process['result'] = result
