
"""
InsultFilter service implemented over Redis (Work Queue pattern):
- Clients enqueue filter_text or get_texts requests
- Service pops tasks, processes them, stores filtered texts in a Redis list
- Responds via per-request response channels
"""
import redis
import json

r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

REQ_QUEUE = 'insult_filter:requests'
RESULT_LIST = 'insult_filter:results'

print(f"[Filter] Redis-based InsultFilter running. Listening for tasks on '{REQ_QUEUE}'.")

while True:
    _, msg = r.blpop(REQ_QUEUE)
    try:
        req = json.loads(msg)
        method = req.get('method')
        result = None
        if method == 'filter_text':
            text = req.get('text', '')
            insults = set(r.smembers('insult_service:insults'))
            words = text.split()
            filtered_words = ['CENSURADO' if w.lower() in insults else w for w in words]
            filtered = ' '.join(filtered_words)
            r.rpush(RESULT_LIST, filtered)
            result = filtered
        elif method == 'get_texts':
            result = r.lrange(RESULT_LIST, 0, -1)
        else:
            result = 'Método desconocido'
    except Exception as e:
        result = f'Error procesando tarea: {e}'
        req = req if 'req' in locals() else {}
    # Publish response
    resp_msg = json.dumps({'id': req.get('id'), 'result': result})
    response_channel = req.get('response_channel')
    if response_channel:
        r.publish(response_channel, resp_msg)