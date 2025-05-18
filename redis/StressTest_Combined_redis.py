
"""
Benchmark simple de Redis-based services para InsultService e InsultFilter.
"""
import time
import redis
import json
import uuid

# Configuración Redis
db = 0
r = redis.Redis(host='localhost', port=6379, db=db, decode_responses=True)

CALLS = 100      # número de peticiones para benchmark

# -----------------------------------------------------------------------------
# Función genérica de RPC Redis (cola + canal de respuesta)
# -----------------------------------------------------------------------------
def send_req(queue, payload, timeout=5):
    """
    Envía payload ({method: ..., ...}) a la cola `queue` y espera respuesta en un canal único.
    """
    req_id = str(uuid.uuid4())
    resp_ch = f"resp:{req_id}"
    payload.update({'id': req_id, 'response_channel': resp_ch})
    pubsub = r.pubsub()
    pubsub.subscribe(resp_ch)
    # Encolar petición
    r.rpush(queue, json.dumps(payload))
    # Esperar respuesta o timeout
    start = time.time()
    for msg in pubsub.listen():
        if msg['type'] == 'message':
            resp = json.loads(msg['data'])
            if resp.get('id') == req_id:
                pubsub.unsubscribe(resp_ch)
                return resp.get('result')
        if time.time() - start > timeout:
            pubsub.unsubscribe(resp_ch)
            raise TimeoutError(f"Timeout en {queue} para petición {req_id}")

# -----------------------------------------------------------------------------
# Benchmark InsultService
# -----------------------------------------------------------------------------
def benchmark_insults(calls=CALLS):
    print("=== Benchmark InsultService ===")
    errors = 0
    t0 = time.perf_counter()
    for i in range(1, calls + 1):
        try:
            # Alterna entre get_insults y add_insult
            if i % 10 == 0:
                send_req('insult_service:requests', {'method':'add_insult', 'insult':f'insulto_{i}'})
            else:
                send_req('insult_service:requests', {'method':'get_insults'})
        except Exception:
            errors += 1
        # Progreso
        if i % (calls // 4) == 0:
            print(f"[InsultService] {i}/{calls} solicitudes completadas")
    elapsed = time.perf_counter() - t0
    print(f"--- RESULTADOS InsultService ---")
    print(f"Peticiones totales : {calls}")
    print(f"Errores            : {errors}")
    print(f"Tiempo total       : {elapsed:.2f} s")
    print(f"Tiempo medio/call  : {elapsed/calls:.4f} s")

# -----------------------------------------------------------------------------
# Benchmark InsultFilter
# -----------------------------------------------------------------------------
def benchmark_filter(calls=CALLS):
    print("\n=== Benchmark InsultFilter ===")
    errors = 0
    t0 = time.perf_counter()
    for i in range(1, calls + 1):
        try:
            text = "Este texto es tonto de prueba"
            send_req('insult_filter:requests', {'method':'filter_text', 'text': text})
        except Exception:
            errors += 1
        # Progreso
        if i % (calls // 4) == 0:
            print(f"[InsultFilter] {i}/{calls} solicitudes completadas")
    elapsed = time.perf_counter() - t0
    print(f"--- RESULTADOS InsultFilter ---")
    print(f"Peticiones totales : {calls}")
    print(f"Errores            : {errors}")
    print(f"Tiempo total       : {elapsed:.2f} s")
    print(f"Tiempo medio/call  : {elapsed/calls:.4f} s")

# -----------------------------------------------------------------------------
# Punto de entrada
def main():
    benchmark_insults()
    benchmark_filter()

if __name__ == '__main__':
    main()
