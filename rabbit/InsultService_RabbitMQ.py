# InsultService_RabbitMQ.py
import threading, time, json, random, pika, redis

RABBITMQ_URL = 'amqp://guest:guest@172.19.16.1:5672/'
RPC_QUEUE    = 'insult_service_rpc'
EXCHANGE     = 'insult_exchange'
REDIS_KEY    = 'insults'

def rpc_server():
    # Servidor RPC con su propia conexión
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch   = conn.channel()
    ch.queue_declare(queue=RPC_QUEUE, durable=True)
    ch.exchange_declare(exchange=EXCHANGE, exchange_type='fanout', durable=True)
    ch.basic_qos(prefetch_count=1)

    def on_rpc(ch, method, props, body):
        req = json.loads(body)
        if req.get('action') == 'add':
            insult = req.get('insult','').strip()
            added  = redis_client.sadd(REDIS_KEY, insult)
            resp   = {'status':'ok','added':bool(added)}
        elif req.get('action') == 'list':
            insults = [i.decode() for i in redis_client.smembers(REDIS_KEY)]
            resp    = {'status':'ok','insults':insults}
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
    print("[Service] RPC server started")
    ch.start_consuming()

def broadcaster():
    # Cada broadcaster abre su propia conexión
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch   = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type='fanout', durable=True)

    while True:
        insults = [i.decode() for i in redis_client.smembers(REDIS_KEY)]
        if insults:
            insult = random.choice(insults)
            ch.basic_publish(exchange=EXCHANGE, routing_key='', body=insult)
            print(f"[Broadcast] {insult}")
        time.sleep(5)

if __name__=='__main__':
    # Inicia el broadcaster en hilo aparte
    t = threading.Thread(target=broadcaster, daemon=True)
    t.start()
    # Y el RPC server en el hilo principal
    rpc_server()
