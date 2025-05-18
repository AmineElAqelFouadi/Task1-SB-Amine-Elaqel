# InsultConsumer_RabbitMQ.py
import json
import pika
import redis

RABBITMQ_URL = 'amqp://guest:guest@localhost:5672/'
INSULT_QUEUE = 'insult_queue'
REDIS_KEY    = 'insults'

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def callback(ch, method, properties, body):
    data = json.loads(body)
    insult = data.get('insult', '').strip()
    added = redis_client.sadd(REDIS_KEY, insult)
    if added:
        print(f"[Consumer] New insult stored: {insult}")
    else:
        print(f"[Consumer] Insult already exists: {insult}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

def main():
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch = conn.channel()
    ch.queue_declare(queue=INSULT_QUEUE, durable=True)
    ch.basic_qos(prefetch_count=1)
    ch.basic_consume(queue=INSULT_QUEUE, on_message_callback=callback)
    print("[Consumer] Waiting for insults…")
    ch.start_consuming()

if __name__ == '__main__':
    main()
