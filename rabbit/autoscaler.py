import redis
import multiprocessing
import time
import os
import math
import requests
import pika
import csv

# Configuración
TEXT_QUEUE = "insult_filter_queue"
MAX_WORKERS = 50
TARGET_RESPONSE_TIME = 2.0   # segundos
CAPACITY_PER_WORKER = 250    # mensajes/seg (ajusta a tu caso real)
PROCESSING_TIME = 0.04       # tiempo medio de proceso por mensaje (en segundos, ejemplo)
RABBITMQ_API = "http://localhost:15672/api/queues/%2F/insult_filter_queue"

def get_rabbitmq_backlog():
    # Devuelve backlog actual usando la API HTTP de RabbitMQ
    try:
        response = requests.get(RABBITMQ_API, auth=("guest", "guest"))
        if response.status_code == 200:
            data = response.json()
            return int(data['messages'])
        else:
            return 0
    except Exception as e:
        print(f"Error accediendo RabbitMQ API: {e}")
        return 0

def filter_worker():
    # El worker normal, puedes importar de tu InsultFilter si lo prefieres
    import InsultFilter_RabbitMQ
    InsultFilter_RabbitMQ.filter_worker()

def autoscale():
    current_workers = 1
    worker_pool = []

    # Prepara CSV
    csvfile = open("scaling_results.csv", "w", newline='')
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(["timestamp", "backlog", "processed", "arrival_rate", "desired_workers", "current_workers"])
    processed_last = 0
    last_time = time.time()

    # Arranca primer worker
    p = multiprocessing.Process(target=filter_worker)
    p.start()
    worker_pool.append(p)

    print("[Autoscaler] Arrancado con 1 worker(s)")

    while True:
        backlog = get_rabbitmq_backlog()
        now = time.time()
        elapsed = now - last_time

        # Estima mensajes procesados en este ciclo (solo para logging)
        processed = 0  # Lo puedes mejorar si tienes métrica real, aquí placeholder

        # Estima arrival rate (λ): podrías enviar muchos mensajes de prueba para simular carga
        # Aquí simplemente le damos un valor fijo de ejemplo
        arrival_rate = 200  # mensajes/seg (AJUSTA O SIMULA TU TEST)

        # Calcula número de workers según la fórmula del backlog
        # N = ceil((B + (λ x Tr)) / C)
        desired_workers = math.ceil((backlog + (arrival_rate * TARGET_RESPONSE_TIME)) / CAPACITY_PER_WORKER)
        desired_workers = max(1, min(desired_workers, MAX_WORKERS))

        # Escala procesos: si faltan, crea más; si sobran, termina algunos
        if desired_workers > current_workers:
            for _ in range(desired_workers - current_workers):
                p = multiprocessing.Process(target=filter_worker)
                p.start()
                worker_pool.append(p)
            print(f"[Autoscaler] ↑ Scale up: {current_workers} → {desired_workers}")
        elif desired_workers < current_workers:
            for _ in range(current_workers - desired_workers):
                proc = worker_pool.pop()
                proc.terminate()
            print(f"[Autoscaler] ↓ Scale down: {current_workers} → {desired_workers}")
        current_workers = desired_workers

        # Guarda en CSV
        csvwriter.writerow([round(now,2), backlog, processed, arrival_rate, desired_workers, current_workers])
        csvfile.flush()

        last_time = now
        time.sleep(2)  # Ciclo de control cada 2 segundos

if __name__ == "__main__":
    autoscale()
