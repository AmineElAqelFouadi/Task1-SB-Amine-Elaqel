# ============================
# client_demo_redis.py
# ============================
"""
Demo script for both Redis-based services.
"""
import threading
import time
import redis
import json
import uuid

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# ----------------------------------------------------------------------------
# Helper: send RPC over Redis
# ----------------------------------------------------------------------------
def send_request(queue, payload, timeout=5):
    # payload must include a unique 'id'
    req_id = str(uuid.uuid4())
    resp_channel = f"resp:{req_id}"
    payload.update({'id': req_id, 'response_channel': resp_channel})
    pubsub = r.pubsub()
    pubsub.subscribe(resp_channel)
    # Enqueue request
    r.rpush(queue, json.dumps(payload))
    # Wait for response
    start = time.time()
    for message in pubsub.listen():
        if message['type'] == 'message':
            resp = json.loads(message['data'])
            if resp.get('id') == req_id:
                pubsub.unsubscribe(resp_channel)
                return resp.get('result')
        if time.time() - start > timeout:
            pubsub.unsubscribe(resp_channel)
            raise TimeoutError('Timeout esperando respuesta')

# ----------------------------------------------------------------------------
# Demo InsultFilter
# ----------------------------------------------------------------------------
def demo_filter_service():
    print("=== Testing InsultFilter Service (Redis) ===")
    samples = ["Hola tonto", "Esto no es bobo", "Sin insultos aquí"]
    for text in samples:
        filtered = send_request('insult_filter:requests', {'method': 'filter_text', 'text': text})
        print(f"Original: {text} -> Filtrado: {filtered}")
    history = send_request('insult_filter:requests', {'method': 'get_texts'})
    print("Histórico de textos filtrados:")
    for i, t in enumerate(history, 1):
        print(f"  {i}. {t}")
    print()

# ----------------------------------------------------------------------------
# Demo InsultService
# ----------------------------------------------------------------------------
def demo_insult_service():
    print("=== Testing InsultService (Redis) ===")
    # Add insults
    insults = ["tonto", "bobo", "burro"]
    for insult in insults:
        resp = send_request('insult_service:requests', {'method': 'add_insult', 'insult': insult})
        print(f"add_insult('{insult}') -> {resp}")
    # List insults
    current = send_request('insult_service:requests', {'method': 'get_insults'})
    print(f"Insults in service: {current}")
    # Subscribe to broadcasts
    channel = send_request('insult_service:requests', {'method': 'subscribe'})
    print(f"Subscribed to channel: {channel}")
    def listen():
        pubsub = r.pubsub()
        pubsub.subscribe(channel)
        for msg in pubsub.listen():
            if msg['type'] == 'message':
                print(f"[Broadcast] {msg['data']}")
    listener = threading.Thread(target=listen, daemon=True)
    listener.start()
    print("Esperando a recibir insultos durante 15 segundos...")
    time.sleep(15)
    print("Demo InsultService terminada.\n")

if __name__ == '__main__':
    demo_filter_service()
    demo_insult_service()