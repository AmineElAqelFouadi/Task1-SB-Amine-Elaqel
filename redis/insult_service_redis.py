# ============================
# insult_service_redis.py
# ============================
"""
InsultService implemented over Redis:
- Stores insults in a Redis set
- Handles RPC via a request queue and per-request response channels
- Broadcasts random insults every 5 seconds on a Pub/Sub channel
"""
import redis
import threading
import time
import random
import json
import uuid

# Redis connection (default localhost:6379)
r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Redis keys and channels
INSULT_SET = 'insult_service:insults'
REQ_QUEUE = 'insult_service:requests'
BROADCAST_CHANNEL = 'insult_service:broadcast'

# Broadcaster thread: publish a random insult every 5 seconds
def _broadcaster():
    while True:
        insults = list(r.smembers(INSULT_SET))
        if insults:
            insult = random.choice(insults)
            r.publish(BROADCAST_CHANNEL, insult)
        time.sleep(5)

threading.Thread(target=_broadcaster, daemon=True).start()

print(f"[Service] Redis-based InsultService running. Listening for requests on '{REQ_QUEUE}'.")

# Main RPC loop: BLPOP on REQ_QUEUE
while True:
    _, msg = r.blpop(REQ_QUEUE)
    try:
        req = json.loads(msg)
        method = req.get('method')
        resp = None
        if method == 'add_insult':
            insult = req.get('insult')
            added = r.sadd(INSULT_SET, insult)
            resp = f"Insulto '{insult}' {'añadido' if added else 'ya existente'}"
        elif method == 'get_insults':
            resp = list(r.smembers(INSULT_SET))
        elif method == 'subscribe':
            # return broadcast channel name
            resp = BROADCAST_CHANNEL
        else:
            resp = 'Método desconocido'
    except Exception as e:
        resp = f'Error procesando petición: {e}'
        req = req if 'req' in locals() else {}
    # Send response back
    resp_msg = json.dumps({'id': req.get('id'), 'result': resp})
    response_channel = req.get('response_channel')
    if response_channel:
        r.publish(response_channel, resp_msg)

