#!/usr/bin/env python3
"""
Multi-nodes static scaling performance analysis.
Stress-test de InsultFilter e InsultService usando 1, 2 y 3 nodos,
y cálculo de speedup S = T1/TN.
"""
import sys
import time
import subprocess
from threading import Lock
from xmlrpc.client import ServerProxy
from concurrent.futures import ThreadPoolExecutor

# Configuración de scripts y puertos
FILTER_SCRIPT = "insult_filter.py"
SERVICE_SCRIPT = "insult_service.py"
FILTER_PORTS  = [8001, 8002, 8003]
SERVICE_PORTS = [9001, 9002, 9003]
NUM_REQUESTS  = 100
MAX_WORKERS   = 50


def start_nodes(script, ports, tag):
    procs = []
    for port in ports:
        p = subprocess.Popen(
            [sys.executable, "-u", script, str(port)],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        procs.append(p)
    return procs


def wait_for_startup(processes, tag, timeout=5.0):
    start = time.time()
    pending = processes.copy()
    while pending and time.time() - start < timeout:
        for p in pending[:]:
            line = p.stdout.readline()
            if line:
                print(line.strip())
                if f"[{tag}]" in line and "Nodo listo" in line:
                    pending.remove(p)
    if pending:
        raise RuntimeError(f"Algunos {tag} no arrancaron correctamente.")


def stress_test(ports, method, tag, payload_func):
    # 1) Creamos un proxy por nodo y lock
    proxies = [ServerProxy(f"http://localhost:{port}/", allow_none=True)
               for port in ports]
    locks = [Lock() for _ in proxies]

    def task(i):
        idx = i % len(proxies)
        with locks[idx]:
            return getattr(proxies[idx], method)(payload_func(i))

    print(f"\n[{tag}] Test con {len(ports)} nodo(s)...")
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(task, i) for i in range(NUM_REQUESTS)]
        for f in futures:
            f.result()
    duration = time.time() - t0
    print(f"[{tag}] {NUM_REQUESTS} peticiones en {duration:.3f}s")
    return duration


def main():
    # 1) Arrancamos nodos de Filter y Service
    filter_procs  = start_nodes(FILTER_SCRIPT, FILTER_PORTS,  "Filter")
    service_procs = start_nodes(SERVICE_SCRIPT, SERVICE_PORTS, "Service")

    # 2) Esperamos a que todos arranquen
    try:
        wait_for_startup(filter_procs,  "Filter")
        wait_for_startup(service_procs, "Service")
    except Exception as e:
        print(e)
        for p in filter_procs + service_procs:
            p.kill()
        sys.exit(1)

    # 3) Dejamos estabilizar
    time.sleep(1)

    # 4) Ejecutamos tests
    results = {"Filter": {}, "Service": {}}

    # Filter tests
    for n in [1, 2, 3]:
        results["Filter"][n] = stress_test(
            FILTER_PORTS[:n], "filtrar_texto", "Filter", lambda i: "Hola tonto prueba"
        )

    # Service tests
    for n in [1, 2, 3]:
        results["Service"][n] = stress_test(
            SERVICE_PORTS[:n], "add_insulto", "Service", lambda i: f"insulto_{i}"
        )

    # 5) Calculamos speedups
    print("\n=== Speedup ===")
    for tag in ["Filter", "Service"]:
        T1 = results[tag][1]
        print(f"\n{tag}: T₁ = {T1:.3f}s")
        for n in [2, 3]:
            TN = results[tag][n]
            S  = T1 / TN
            print(f"  {n} nodos → Tₙ = {TN:.3f}s → Speedup = {S:.2f}×")
    time.sleep(30)
    # 6) Terminamos procesos
    for p in filter_procs + service_procs:
        p.kill()

if __name__ == "__main__":
    main()
