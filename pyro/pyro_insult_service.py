#!/usr/bin/env python3
import sys
import Pyro4, threading, time, random

@Pyro4.expose
class InsultService(object):
    def __init__(self):
        self.insults = set()
        self.subscribers = []
        self._start_broadcaster()

    def add_insulto(self, insulto):
        if insulto not in self.insults:
            self.insults.add(insulto)
            return f"Insulto '{insulto}' añadido"
        return "Insulto ya existente"

    def get_insults(self):
        return list(self.insults)

    def subscribe(self, callback_uri):
        if callback_uri not in self.subscribers:
            self.subscribers.append(callback_uri)
            return "Suscripción exitosa"
        return "Ya estabas suscrito"

    def _start_broadcaster(self):
        def loop():
            while True:
                if self.insults and self.subscribers:
                    insult = random.choice(list(self.insults))
                    for uri in self.subscribers.copy():
                        try:
                            proxy = Pyro4.Proxy(uri)
                            proxy.filtrar_texto(insult)
                        except Pyro4.errors.CommunicationError:
                            self.subscribers.remove(uri)
                time.sleep(5)  # Broadcast every 5 seconds
        threading.Thread(target=loop, daemon=True).start()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    with Pyro4.Daemon(host="localhost", port=port) as daemon:
        service = InsultService()
        uri = daemon.register(service, objectId="InsultService")
        print(f"[Service] Nodo Pyro listo en puerto {port}, URI: {uri}")
        daemon.requestLoop()

if __name__ == "__main__":
    main()