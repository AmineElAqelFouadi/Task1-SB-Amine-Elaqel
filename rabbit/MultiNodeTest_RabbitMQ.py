#!/usr/bin/env python3
"""
MultiNodeTest_RabbitMQ.py

Escalado estático (1, 2 y 3 nodos) para:
  • InsultService_RabbitMQ (RPC)      → concurrente en N hilos
  • InsultFilter_RabbitMQ (Work Queue)

Salida estilo consola:
  [Filter] Test con N nodo(s)...
  [Filter] 100 peticiones en 0.096s

  [Service] Test con N nodo(s)...
  [Service] 100 peticiones en 0.089s

=== Speedup ===
Filter: T1 = 0.096s
2 nodos -> T2 = 0.088s -> Speedup = 1.09x
3 nodos -> T3 = 0.079s -> Speedup = 1.22x

Service: T1 = 0.098s
2 nodos -> T2 = 0.062s -> Speedup = 1.58x
3 nodos -> T3 = 0.045s -> Speedup = 2.18x
"""

import sys, time, uuid, json, subprocess, threading
import redis, pika

# Parámetros
RABBITMQ_URL   = 'amqp://guest:guest@localhost:5672/'
REDIS_HOST     = 'localhost'
REDIS_PORT     = 6379

SERVICE_SCRIPT = 'InsultService_RabbitMQ.py'
FILTER_SCRIPT  = 'InsultFilter_RabbitMQ.py'

SERVICE_RPC    = 'insult_service_rpc'
FILTER_QUEUE   = 'insult_filter_queue'
FILTER_RPC     = 'insult_filter_rpc'

CALLS_SERVICE  = 100
CALLS_FILTER   = 100
NODE_COUNTS    = [1, 2, 3]
WAIT_START     = 2  # segundos para levantar nodos

def rpc_call(channel, queue, payload, timeout=10):
    corr_id = str(uuid.uuid4())
    result   = channel.queue_declare(queue='', exclusive=True)
    cb_queue = result.method.queue
    response = None

    def on_response(ch, method, props, body):
        nonlocal response
        if props.correlation_id == corr_id:
            response = json.loads(body)

    channel.basic_consume(queue=cb_queue, on_message_callback=on_response, auto_ack=True)
    channel.basic_publish(
        exchange='', routing_key=queue,
        properties=pika.BasicProperties(
            reply_to=cb_queue,
            correlation_id=corr_id
        ),
        body=json.dumps(payload)
    )
    start = time.time()
    while response is None and time.time() - start < timeout:
        channel.connection.process_data_events(time_limit=0.01)
    return response

def start_nodes(script, count):
    procs = []
    for _ in range(count):
        p = subprocess.Popen([sys.executable, script],
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        procs.append(p)
    return procs

def stop_nodes(procs):
    for p in procs:
        p.terminate()
    for p in procs:
        p.wait(timeout=2)

def benchmark_filter(nodes):
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    r.delete('filtered_texts')

    procs = start_nodes(FILTER_SCRIPT, nodes)
    time.sleep(WAIT_START)

    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch   = conn.channel()

    t0 = time.perf_counter()
    for i in range(1, CALLS_FILTER+1):
        ch.basic_publish(
            exchange='',
            routing_key=FILTER_QUEUE,
            body=json.dumps({'text': f'Texto {i} con insulto srv{nodes}'})
        )

    # espera a que Redis reciba todos
    while r.llen('filtered_texts') < CALLS_FILTER:
        time.sleep(0.01)
    elapsed = time.perf_counter() - t0

    conn.close()
    stop_nodes(procs)
    return elapsed

def benchmark_service(nodes):
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)
    r.delete('insults')

    procs = start_nodes(SERVICE_SCRIPT, nodes)
    time.sleep(WAIT_START)

    # calculamos cuántas llamadas tocan por hilo
    base, extra = divmod(CALLS_SERVICE, nodes)
    counts = [base + (1 if i < extra else 0) for i in range(nodes)]

    def worker(n_calls, idx):
        conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
        ch   = conn.channel()
        # pre-carga en el primero
        if idx == 0:
            rpc_call(ch, SERVICE_RPC, {'action':'add','insult':'base'})
        for j in range(n_calls):
            payload = {'action':'list'} if j % 2 else {'action':'add', 'insult': f'srv{nodes}_{idx}_{j}'}
            rpc_call(ch, SERVICE_RPC, payload)
        conn.close()

    threads = []
    t0 = time.perf_counter()
    for idx, n_calls in enumerate(counts):
        t = threading.Thread(target=worker, args=(n_calls, idx), daemon=True)
        t.start()
        threads.append(t)
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - t0

    stop_nodes(procs)
    return elapsed

if __name__ == '__main__':
    times_f = {}
    times_s = {}

    # --- Filter ---
    for n in NODE_COUNTS:
        print(f"[Filter] Test con {n} nodo(s)...")
        tf = benchmark_filter(n)
        times_f[n] = tf
        print(f"[Filter] {CALLS_FILTER} peticiones en {tf:.3f}s\n")

    # --- Service ---
    for n in NODE_COUNTS:
        print(f"[Service] Test con {n} nodo(s)...")
        ts = benchmark_service(n)
        times_s[n] = ts
        print(f"[Service] {CALLS_SERVICE} peticiones en {ts:.3f}s\n")

    # --- Speedup ---
    print("=== Speedup ===\n")

    t1f = times_f[1]
    print(f"Filter: T1 = {t1f:.3f}s")
    for n in NODE_COUNTS[1:]:
        tn = times_f[n]
        print(f"{n} nodos -> T{n} = {tn:.3f}s -> Speedup = {t1f/tn:.2f}x")
    print()

    t1s = times_s[1]
    print(f"Service: T1 = {t1s:.3f}s")
    for n in NODE_COUNTS[1:]:
        tn = times_s[n]
        print(f"{n} nodos -> T{n} = {tn:.3f}s -> Speedup = {t1s/tn:.2f}x")
