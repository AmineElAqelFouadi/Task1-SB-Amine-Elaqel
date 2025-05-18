#!/usr/bin/env python3
import sys
import threading
import time
import Pyro4

# Callback for receiving insult broadcasts
@Pyro4.expose
class InsultReceiver(object):
    def filtrar_texto(self, insulto):
        print(f"[Receiver] Received insult: {insulto}")
        return True


def start_receiver_daemon(port=8002):
    daemon = Pyro4.Daemon(host="localhost", port=port)
    receiver = InsultReceiver()
    uri = daemon.register(receiver, objectId="InsultReceiver")
    print(f"[Receiver] Pyro daemon running on port {port}, URI: {uri}")
    threading.Thread(target=daemon.requestLoop, daemon=True).start()
    return uri


def demo_filter_service(filter_uri):
    print("=== Testing InsultFilter Service ===")
    proxy = Pyro4.Proxy(filter_uri)
    samples = ["Hola tonto", "Esto no es bobo", "Sin insultos aquí"]
    for text in samples:
        filtered = proxy.filtrar_texto(text)
        print(f"Original: {text} -> Filtrado: {filtered}")
    history = proxy.obtener_textos()
    print("Histórico de textos filtrados:")
    for i, t in enumerate(history, 1):
        print(f"  {i}. {t}")
    print()


def demo_insult_service(service_uri, callback_uri):
    print("=== Testing InsultService ===")
    proxy = Pyro4.Proxy(service_uri)
    insults = ["tonto", "bobo", "burro"]
    for insult in insults:
        resp = proxy.add_insulto(insult)
        print(f"add_insulto('{insult}') -> {resp}")
    current = proxy.get_insults()
    print(f"Insults in service: {current}")
    sub_resp = proxy.subscribe(callback_uri)
    print(f"subscribe('{callback_uri}') -> {sub_resp}")
    print("Esperando a recibir insultos durante 15 segundos...")
    time.sleep(15)
    print("Demo InsultService terminada.\n")


if __name__ == "__main__":
    callback_uri = start_receiver_daemon(port=8002)
    time.sleep(1)
    filter_uri = f"PYRO:InsultFilter@localhost:8001"
    service_uri = f"PYRO:InsultService@localhost:9000"
    demo_filter_service(filter_uri)
    demo_insult_service(service_uri, callback_uri)
    print("Demo completa.")