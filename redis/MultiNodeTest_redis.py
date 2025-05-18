# ============================
# MultiNodeTest_redis.py
# ============================
"""
Static scaling performance analysis for Redis-based services.
Spawn multiple worker instances to test speedup.
"""
import subprocess
import time
import sys
import uuid
import redis
import json
from concurrent.futures import ThreadPoolExecutor

NUM_REQUESTS = 100
MAX_WORKERS = 50

# Scripts to launch
FILTER_SCRIPT = 'insult_filter_redis.py'
SERVICE_SCRIPT = 'insult_service_redis.py'

def start_processes(script, count):
    procs = []
    for _ in range(count):
        p = subprocess.Popen([sys.executable, script], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        procs.append(p)
    return procs

# Helper request function (like client_demo)
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
def send_req(queue, payload):
    req_id = str(uuid.uuid4())
    resp_ch = f"resp:{req_id}"
    payload.update({'id': req_id, 'response_channel': resp_ch})
    pubsub = r.pubsub()
    pubsub.subscribe(resp_ch)
    r.rpush(queue, json.dumps(payload))
    for msg in pubsub.listen():
        if msg['type']=='message':
            resp = json.loads(msg['data'])
            if resp.get('id')==req_id:
                pubsub.unsubscribe(resp_ch)
                return resp.get('result')

# Stress test logic

def stress_test(queue, method_key, tag, payload_func, node_count):
    print(f"\n[{tag}] Test con {node_count} nodo(s)...")
    start = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(send_req, queue, payload_func(i)) for i in range(NUM_REQUESTS)]
        for f in futures:
            f.result()
    duration = time.time()-start
    print(f"[{tag}] {NUM_REQUESTS} peticiones en {duration:.3f}s")
    return duration

if __name__=='__main__':
    results = {'Filter': {}, 'Service': {}}
    # Static scaling: 1,2,3 workers
    for tag, script, queue, payload in [
        ('Filter', FILTER_SCRIPT, 'insult_filter:requests', lambda i: {'method':'filter_text', 'text':'Hola tonto prueba'}),
        ('Service', SERVICE_SCRIPT, 'insult_service:requests', lambda i: {'method':'add_insult', 'insult':f'insulto_{i}'})
    ]:
        for n in [1,2,3]:
            procs = start_processes(script, n)
            time.sleep(1)
            results[tag][n] = stress_test(queue, 'method', tag, payload, n)
            for p in procs: p.kill()
    # Compute speedups
    print("\n=== Speedup ===")
    for tag in ['Filter','Service']:
        T1 = results[tag][1]
        print(f"\n{tag}: T₁ = {T1:.3f}s")
        for n in [2,3]:
            TN = results[tag][n]
            print(f"  {n} nodos → Tₙ = {TN:.3f}s → Speedup = {T1/TN:.2f}×")
