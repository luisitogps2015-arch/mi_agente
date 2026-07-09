import json
import time
import subprocess
import os
import mcp_server

def ejecutar_tareas():
    archivo_tareas = "tareas.json"
    if not os.path.exists(archivo_tareas):
        return

    with open(archivo_tareas, "r") as f:
        try:
            tareas = json.load(f)
            # Aseguramos que 'tareas' sea una lista
            if not isinstance(tareas, list):
                print("El archivo JSON no es una lista.")
                return
        except Exception as e:
            print(f"Error al leer JSON: {e}")
            return

    for tarea in tareas:
        # AQUÍ ESTÁ EL CAMBIO: Verificamos si es un diccionario
        if isinstance(tarea, dict) and tarea.get("estado") == "activo":
            print(f"Ejecutando tarea: {tarea.get('descripcion', 'Sin descripción')}")
            try:
                resultado = subprocess.check_output(tarea['tarea'], shell=True, text=True)
                mcp_server.bot.send_message(
                    mcp_server.TU_CHAT_ID, 
                    f"🔔 *Alerta:* {tarea.get('descripcion', 'Tarea')}\n\n{resultado}", 
                    parse_mode="Markdown"
                )
            except Exception as e:
                error_msg = f"⚠️ Error en tarea {tarea.get('descripcion', 'Tarea')}: {e}"
                print(error_msg)
                try:
                    mcp_server.bot.send_message(mcp_server.TU_CHAT_ID, error_msg)
                except:
                    pass

if __name__ == "__main__":
    print("Monitor de alertas iniciado (cron_runner.py)...")
    while True:
        ejecutar_tareas()
        time.sleep(300)
