#!/usr/bin/env python3
"""
benchmark_rpc.py

Stress-test sencillo para:
  • InsultService (add_insult + insult_me)
  • InsultFilter  (filter_text)

Funciona con:
  - insult_service.py (localhost:8000)
  - insult_filter.py  (localhost:8001)
"""
import xmlrpc.client
import time

# Cantidad de llamadas por servicio
CALLS = 100

def benchmark_insults(host="localhost", port=8000, calls=CALLS):
    url = f"http://{host}:{port}"
    svc = xmlrpc.client.ServerProxy(url, allow_none=True)
    
    # Añadir varios insultos de prueba
    test_insults = ["tonto"]
    for insult in test_insults:
        svc.add_insult(insult)  # Usar el método real del servicio

    errors = 0
    t0 = time.perf_counter()
    for i in range(1, calls + 1):
        try:
            # Obtener lista completa de insultos
            svc.get_insults()
            
            # Añadir nuevo insulto (cada 10 iteraciones)
            if i % 10 == 0:
                svc.add_insult(f"insulto_{i}")
            
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
    url = f"http://{host}:{port}"
    svc = xmlrpc.client.ServerProxy(url, allow_none=True)

    # Frases de prueba mejoradas
    test_phrases = [
        "Eres un tonto del culo"
    ]

    errors = 0
    t0 = time.perf_counter()
    
    for i in range(calls):
        try:
            # Selección cíclica de frases
            phrase = test_phrases[i % len(test_phrases)]
            response = svc.filtrar_texto(f"{phrase} - iteración {i+1}")
            
            # Verificación básica de respuesta
            if "CENSURADO" not in response:
                raise ValueError("Fallo en el filtrado")
                
        except Exception as e:
            errors += 1
            print(f"[InsultFilter] Error #{i+1}: {str(e)[:50]}...")
            
        # Progress cada 25%
        if (i+1) % (calls//4) == 0:
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
    # Lanza los tests uno tras otro
    benchmark_insults()
    benchmark_filter()
    
    
