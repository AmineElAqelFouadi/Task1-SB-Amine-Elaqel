import threading, json, re, pika, redis

RABBITMQ_URL = 'amqp://guest:guest@172.19.16.1:5672/'
WORK_QUEUE     = 'insult_filter_queue'
RPC_QUEUE      = 'insult_filter_rpc'
REDIS_INSULTS  = 'insults'
REDIS_RESULTS  = 'filtered_texts'

def filter_worker():
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch = conn.channel()
    ch.queue_declare(queue=WORK_QUEUE, durable=True)
    ch.basic_qos(prefetch_count=1)

    def callback(ch, method, props, body):
        # 1) Intentar JSON {"text": "..."}
        try:
            data = json.loads(body)
            text = data.get('text', '')
        except json.JSONDecodeError:
            # No era JSON, tratamos body como texto plano
            text = body.decode()

        # 2) Filtrado de insultos (igual que antes)
        insults = [re.escape(i.decode()) for i in redis_client.smembers(REDIS_INSULTS)]
        if insults:
            pattern = re.compile(r'\b(' + '|'.join(insults) + r')\b', flags=re.IGNORECASE)
            filtered = pattern.sub('CENSORED', text)
        else:
            filtered = text

        redis_client.rpush(REDIS_RESULTS, filtered)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    ch.basic_consume(queue=WORK_QUEUE, on_message_callback=callback)
    print(f"[Filter] Worker {threading.current_thread().name} started")
    ch.start_consuming()

def rpc_server():
    # El servidor RPC también con su propia conexión
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch   = conn.channel()
    ch.queue_declare(queue=RPC_QUEUE, durable=True)
    ch.basic_qos(prefetch_count=1)

    def on_rpc(ch, method, props, body):
        req = json.loads(body)
        if req.get('action') == 'list':
            results = [i.decode() for i in redis_client.lrange(REDIS_RESULTS, 0, -1)]
            resp = {'status':'ok','results':results}
        else:
            resp = {'status':'error','message':'Unknown action'}
        ch.basic_publish(
            exchange='',
            routing_key=props.reply_to,
            properties=pika.BasicProperties(correlation_id=props.correlation_id),
            body=json.dumps(resp)
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)

    ch.basic_consume(queue=RPC_QUEUE, on_message_callback=on_rpc)
    print("[Filter] RPC server started")
    ch.start_consuming()

if __name__=='__main__':
    # Levanta 4 hilos-worker independientes
    for i in range(4):
        t = threading.Thread(target=filter_worker, name=f"Worker-{i+1}", daemon=True)
        t.start()
    # Y arranca el servidor RPC en el hilo principal
    rpc_server()
