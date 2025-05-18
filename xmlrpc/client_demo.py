#!/usr/bin/env python3
import xmlrpc.client
from xmlrpc.server import SimpleXMLRPCServer
import threading
import time

# Receiver para el servicio de insultos
class InsultReceiver:
    def receive_insult(self, insult):
        print(f"[Receiver] Received insult: {insult}")
        return True  # Acknowledge receipt

# Inicia un servidor XML-RPC local para recibir insultos
def start_receiver_server(port=8002):
    receiver = InsultReceiver()
    server = SimpleXMLRPCServer(('localhost', port), allow_none=True, logRequests=False)
    server.register_instance(receiver)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"[Receiver] XMLRPC server running on port {port}")
    return f"http://localhost:{port}/"

# Demo del servicio de filtrado de insultos
def demo_filter_service():
    print("=== Testing InsultFilter Service ===")
    proxy = xmlrpc.client.ServerProxy("http://localhost:8001/", allow_none=True)
    samples = ["Hola tonto", "Esto no es bobo", "Sin insultos aquí"]
    for text in samples:
        filtered = proxy.filtrar_texto(text)
        print(f"Original: {text} -> Filtrado: {filtered}")
    # Obtener histórico
    history = proxy.obtener_textos()
    print("Histórico de textos filtrados:")
    for i, t in enumerate(history, 1):
        print(f"  {i}. {t}")
    print()

# Demo del servicio de gestión y broadcast de insultos
def demo_insult_service(callback_url):
    print("=== Testing InsultService ===")
    proxy = xmlrpc.client.ServerProxy("http://localhost:8000/", allow_none=True)
    # Añadir insultos
    insults = ["tonto", "bobo", "burro"]
    for insult in insults:
        resp = proxy.add_insult(insult)
        print(f"add_insult('{insult}') -> {resp}")
    # Listar insultos
    current = proxy.get_insults()
    print(f"Insults in service: {current}")
    # Suscribirse para recibir insultos
    sub_resp = proxy.subscribe(callback_url)
    print(f"subscribe('{callback_url}') -> {sub_resp}")
    print("Esperando a recibir insultos durante 15 segundos...")
    time.sleep(15)
    print("Demo InsultService terminada.\n")

if __name__ == "__main__":
    # Iniciar el receptor de insultos
    callback = start_receiver_server(port=8002)
    time.sleep(1)  # Asegurar que el servidor esté arriba
    # Ejecutar demos
    demo_filter_service()
    demo_insult_service(callback)
    print("Demo completa.")
