#!/usr/bin/env python3
import time
import Pyro4

CALLS = 100

def benchmark_insults(host="localhost", port=9000, calls=CALLS):
    uri = f"PYRO:InsultService@{host}:{port}"
    svc = Pyro4.Proxy(uri)
    # Inicializar con un insulto base
    svc.add_insulto("tonto")
    errors = 0
    t0 = time.perf_counter()
    for i in range(1, calls + 1):
        try:
            svc.get_insults()
            if i % 10 == 0:
                svc.add_insulto(f"insulto_{i}")
        except Exception as e:
            errors += 1
            print(f"[InsultService] Error #{i}: {str(e)[:50]}...")
        if i % (calls // 4) == 0:
            print(f"[InsultService] {i}/{calls} requests")
    elapsed = time.perf_counter() - t0
    avg = elapsed / calls
    print(f"\n--- RESULTADOS InsultService ---")
    print(f"Peticiones totales : {calls}")
    print(f"Errores            : {errors}")
    print(f"Tiempo total       : {elapsed:.2f} s")
    print(f"Tiempo medio/call  : {avg:.4f} s\n")
    return elapsed, errors


def benchmark_filter(host="localhost", port=8001, calls=CALLS):
    uri = f"PYRO:InsultFilter@{host}:{port}"
    svc = Pyro4.Proxy(uri)
    test_phrases = ["Eres un tonto del culo"]
    errors = 0
    t0 = time.perf_counter()
    for i in range(calls):
        try:
            phrase = test_phrases[i % len(test_phrases)]
            response = svc.filtrar_texto(f"{phrase} - iteración {i+1}")
            if "CENSURADO" not in response:
                raise ValueError("Fallo en el filtrado")
        except Exception as e:
            errors += 1
            print(f"[InsultFilter] Error #{i+1}: {str(e)[:50]}...")
        if (i+1) % (calls // 4) == 0:
            print(f"[InsultFilter] Progreso: {i+1}/{calls}")
    elapsed = time.perf_counter() - t0
    avg = elapsed / calls
    print(f"\n--- RESULTADOS InsultFilter ---")
    print(f"Peticiones totales : {calls}")
    print(f"Errores            : {errors}")
    print(f"Tiempo total       : {elapsed:.2f} s")
    print(f"Tiempo medio/call  : {avg:.4f} s\n")
    return elapsed, errors

if __name__ == "__main__":
    benchmark_insults()
    benchmark_filter()