from xmlrpc.server import SimpleXMLRPCServer

# Lista de insultos predefinidos
INSULTOS = {"tonto", "bobo"}

# Almacenamiento de textos filtrados
textos_filtrados = []

def filtrar_texto(texto):
    palabras = texto.split()
    filtrado = [
        "CENSURADO" if palabra.lower() in INSULTOS else palabra
        for palabra in palabras
    ]
    resultado = " ".join(filtrado)
    textos_filtrados.append(resultado)
    return resultado

def obtener_textos():
    return textos_filtrados.copy()

if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    try:
        servidor = SimpleXMLRPCServer(
            ("localhost", port), allow_none=True, logRequests=False
        )
        servidor.register_function(filtrar_texto, "filtrar_texto")
        servidor.register_function(obtener_textos, "obtener_textos")
        # Forzamos flush para que salga aun cuando stdout esté piped
        print(f"[Filter] Nodo listo en puerto {port}", flush=True)
        servidor.serve_forever()
    except Exception as e:
        print(f"[Filter] ERROR al arrancar en puerto {port}: {e}", flush=True)
