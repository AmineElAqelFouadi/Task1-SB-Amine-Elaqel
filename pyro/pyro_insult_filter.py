#!/usr/bin/env python3
import sys
import Pyro4

INSULTOS = {"tonto", "bobo"}
textos_filtrados = []

@Pyro4.expose
class InsultFilter(object):
    def filtrar_texto(self, texto):
        palabras = texto.split()
        filtrado = [
            "CENSURADO" if palabra.lower() in INSULTOS else palabra
            for palabra in palabras
        ]
        resultado = " ".join(filtrado)
        textos_filtrados.append(resultado)
        return resultado

    def obtener_textos(self):
        return textos_filtrados.copy()


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    with Pyro4.Daemon(host="localhost", port=port) as daemon:
        filtro = InsultFilter()
        uri = daemon.register(filtro, objectId="InsultFilter")
        print(f"[Filter] Nodo Pyro listo en puerto {port}, URI: {uri}")
        daemon.requestLoop()

if __name__ == "__main__":
    main()