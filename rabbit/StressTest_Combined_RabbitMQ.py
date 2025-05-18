#!/usr/bin/env python3
"""
StressTest_Combined_RabbitMQ.py

Stress-test sencillo para:
  • InsultService_RabbitMQ (RPC + broadcaster)
  • InsultFilter_RabbitMQ (work queue + RPC)

Funciona con:
  - InsultService_RabbitMQ.py
  - InsultFilter_RabbitMQ.py
RabbitMQ + Redis
"""

import time
import uuid
import json
import pika

# Configuración
RABBITMQ_URL = 'amqp://guest:guest@localhost:5672/'
SERVICE_RPC  = 'insult_service_rpc'
FILTER_QUEUE = 'insult_filter_queue'
FILTER_RPC   = 'insult_filter_rpc'
CALLS        = 100

def rpc_call(channel, queue, payload, timeout=10):
    """Envía un payload a queue vía RPC y espera la respuesta."""
    corr_id = str(uuid.uuid4())
    # cola anónima de respuesta
    result = channel.queue_declare(queue='', exclusive=True)
    callback_queue = result.method.queue
    response = None

    def on_response(ch, method, props, body):
        nonlocal response
        if props.correlation_id == corr_id:
            response = json.loads(body)

    channel.basic_consume(
        queue=callback_queue,
        on_message_callback=on_response,
        auto_ack=True
    )
    channel.basic_publish(
        exchange='',
        routing_key=queue,
        properties=pika.BasicProperties(
            reply_to=callback_queue,
            correlation_id=corr_id
        ),
        body=json.dumps(payload)
    )
    start = time.time()
    while response is None and time.time() - start < timeout:
        channel.connection.process_data_events(time_limit=0.1)
    return response

def benchmark_insults(calls=CALLS):
    """Mide rendimiento de InsultService vía RPC."""
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch   = conn.channel()

    errors = 0
    # Pre-carga un insulto base
    rpc_call(ch, SERVICE_RPC, {'action':'add', 'insult':'tonto'})

    t0 = time.perf_counter()
    for i in range(1, calls + 1):
        try:
            # Listar insultos
            rpc_call(ch, SERVICE_RPC, {'action':'list'})
            # Cada 10 llamadas, añade un insulto nuevo
            if i % 10 == 0:
                rpc_call(ch, SERVICE_RPC, {'action':'add', 'insult':f'insulto_{i}'})
        except Exception as e:
            errors += 1
            print(f"[InsultService] Error #{i}: {e}")
        if i % (calls // 4) == 0:
            print(f"[InsultService] {i}/{calls} requests processed")

    elapsed = time.perf_counter() - t0
    avg     = elapsed / calls

    print("\n--- RESULTADOS InsultService (RabbitMQ) ---")
    print(f"Peticiones totales : {calls}")
    print(f"Errores            : {errors}")
    print(f"Tiempo total       : {elapsed:.2f} s")
    print(f"Tiempo medio/call  : {avg:.4f} s\n")

    conn.close()
    return elapsed, errors

def benchmark_filter(calls=CALLS):
    """Mide rendimiento de InsultFilter vía Work Queue + RPC."""
    conn = pika.BlockingConnection(pika.URLParameters(RABBITMQ_URL))
    ch   = conn.channel()

    errors = 0
    test_phrases = ["Eres un tonto del culo"]
    t0 = time.perf_counter()

    for i in range(calls):
        phrase = test_phrases[i % len(test_phrases)]
        payload = {'text': f"{phrase} - iteración {i+1}"}
        try:
            # Publica trabajo en la cola de filtrado
            ch.basic_publish(exchange='', routing_key=FILTER_QUEUE, body=json.dumps(payload))
        except Exception as e:
            errors += 1
            print(f"[InsultFilter] Error publish #{i+1}: {e}")
        if (i + 1) % (calls // 4) == 0:
            print(f"[InsultFilter] {i+1}/{calls} jobs queued")

    # Recupera resultados
    res = rpc_call(ch, FILTER_RPC, {'action':'list'})

    elapsed = time.perf_counter() - t0
    avg     = elapsed / calls

    print("\n--- RESULTADOS InsultFilter (RabbitMQ) ---")
    print(f"Trabajos totales   : {calls}")
    print(f"Errores publish    : {errors}")
    print(f"Tiempo total       : {elapsed:.2f} s")
    print(f"Tiempo medio/job   : {avg:.4f} s\n")

    conn.close()
    return elapsed, errors

if __name__ == "__main__":
    # Lanza ambos benchmarks uno tras otro
    benchmark_insults()
    benchmark_filter()
