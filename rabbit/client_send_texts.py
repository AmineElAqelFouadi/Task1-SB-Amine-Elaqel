import pika
import json
import time
import random

RABBITMQ_URL = 'amqp://guest:guest@172.19.16.1:5672/'
QUEUE_NAME = 'insult_filter_queue'

# Ejemplos de textos, algunos con insultos típicos
TEXTS = [
    "You are a genius!",
    "Eres un tonto",
    "This is awesome.",
    "You are such a bobo",
    "I love programming.",
    "Hello, have a nice day.",
    "You are a loser.",
    "That's clever.",
    "You're a moron.",
    "Keep going, don't give up!"
]

def send_texts(n=1000, delay=0):
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch = conn.channel()
    ch.queue_declare(queue=QUEUE_NAME, durable=True)

    for i in range(n):
        text = random.choice(TEXTS)
        msg = json.dumps({"text": text})
        ch.basic_publish(
            exchange='',
            routing_key=QUEUE_NAME,
            body=msg,
            properties=pika.BasicProperties(delivery_mode=2)  # Persistente
        )
        print(f"Sent ({i+1}): {text}")
        if delay > 0:
            time.sleep(delay)

    conn.close()
    print(f"\nEnviados {n} mensajes a la cola '{QUEUE_NAME}'.")

if __name__ == "__main__":
    send_texts(n=50000, delay=0)
