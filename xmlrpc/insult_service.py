from xmlrpc.server import SimpleXMLRPCServer
import xmlrpc.client
import threading
import time
import random

class InsultService:
    def __init__(self):
        self.insults = set()
        self.subscribers = []
        self._start_broadcaster()

    def _start_broadcaster(self):
        def loop():
            while True:
                if self.insults and self.subscribers:
                    insult = random.choice(list(self.insults))
                    for url in list(self.subscribers):
                        try:
                            with xmlrpc.client.ServerProxy(url) as proxy:
                                proxy.filtrar_texto(insult)
                        except:
                            self.subscribers.remove(url)
                time.sleep(1)
        threading.Thread(target=loop, daemon=True).start()

    def add_insulto(self, insulto):
        if insulto not in self.insults:
            self.insults.add(insulto)
            return f"Insulto '{insulto}' añadido"
        return "Insulto ya existente"

    def get_insults(self):
        return list(self.insults)

    def subscribe(self, url):
        if url not in self.subscribers:
            self.subscribers.append(url)
            return "Suscripción exitosa"
        return "Ya estabas suscrito"

def run_server(port):
    try:
        server = SimpleXMLRPCServer(("localhost", port), allow_none=True, logRequests=False)
        server.register_instance(InsultService())
        # Forzamos flush por mismo motivo
        print(f"[Service] Nodo listo en puerto {port}", flush=True)
        server.serve_forever()
    except Exception as e:
        print(f"[Service] ERROR al arrancar en puerto {port}: {e}", flush=True)

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    run_server(port)
