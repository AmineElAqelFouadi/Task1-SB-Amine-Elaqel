# InsultReceiver_RabbitMQ.py
import pika

RABBITMQ_URL = 'amqp://guest:guest@localhost:5672/'
EXCHANGE     = 'insult_exchange'

def main():
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch = conn.channel()
    ch.exchange_declare(exchange=EXCHANGE, exchange_type='fanout', durable=True)
    result = ch.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    ch.queue_bind(exchange=EXCHANGE, queue=queue_name)

    def callback(ch, method, properties, body):
        print(f"[Receiver] Got insult: {body.decode()}")

    ch.basic_consume(queue=queue_name, on_message_callback=callback, auto_ack=True)
    print("[Receiver] Waiting for broadcasts…")
    ch.start_consuming()

if __name__ == '__main__':
    main()
