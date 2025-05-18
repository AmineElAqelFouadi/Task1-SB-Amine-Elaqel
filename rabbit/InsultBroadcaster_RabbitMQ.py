# InsultBroadcaster_RabbitMQ.py
import time
import random
import pika
import redis

RABBITMQ_URL = 'amqp://guest:guest@localhost:5672/'
EXCHANGE     = 'insult_exchange'
REDIS_KEY    = 'insults'

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def main():
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type='fanout', durable=True)

    while True:
        insults = [i.decode() for i in redis_client.smembers(REDIS_KEY)]
        if insults:
            insult = random.choice(insults)
            ch.basic_publish(exchange=EXCHANGE, routing_key='', body=insult)
            print(f"[Broadcaster] Broadcasted: {insult}")
        else:
            print("[Broadcaster] No insults to broadcast yet.")
        time.sleep(5)

if __name__ == '__main__':
    main()
