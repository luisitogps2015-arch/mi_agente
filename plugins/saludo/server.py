import json
import sys

# --- LÓGICA DE NEGOCIO ORIGINAL ---
def saludar_nombre(nombre):
    return f"Hola, {nombre}!"

# --- INTERFAZ PARA EL MOTOR ---
def run(params):
    """
    Esta es la función que el mcp_server.py buscará.
    'params' viene del JSON que enviaste desde el cliente.
    """
    # Ejemplo: Si el cliente envía {"nombre": "Juan"} en params
    nombre = params.get('nombre', 'Usuario')
    resultado = saludar_nombre(nombre)
    return resultado

# --- MANTENEMOS LA CAPACIDAD DE EJECUCIÓN DIRECTA (Opcional) ---
# Esto permite que puedas probar el plugin manualmente si lo deseas
if __name__ == "__main__":
    try:
        input_data = sys.stdin.read()
        if input_data:
            request = json.loads(input_data)
            # Adaptamos para que llame a 'run' internamente
            resultado = run(request.get('params', {}))
            print(json.dumps({"status": "ok", "result": resultado}))
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
