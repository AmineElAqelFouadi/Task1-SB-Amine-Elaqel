# InsultProducer_RabbitMQ.py
import time
import json
import pika

RABBITMQ_URL = 'amqp://guest:guest@localhost:15672/'
INSULT_QUEUE = 'insult_queue'

# Lista de insultos de ejemplo; puedes ampliarla
INSULTS = [
    "loser", "moron", "tonto", "bobo",
]

def main():
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch = conn.channel()
    ch.queue_declare(queue=INSULT_QUEUE, durable=True)

    idx = 0
    while True:
        insult = INSULTS[idx % len(INSULTS)]
        msg = json.dumps({'insult': insult})
        ch.basic_publish(
            exchange='',
            routing_key=INSULT_QUEUE,
            body=msg,
            properties=pika.BasicProperties(delivery_mode=2)
        )
        print(f"[Producer] Sent insult: {insult}")
        idx += 1
        time.sleep(5)

if __name__ == '__main__':
    main()
