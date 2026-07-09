import json
import os
import subprocess

from task_decomposer import descomponer_tareas


PLUGINS_DIR = "plugins"
PLUGINS_ACTIVOS = "plugins_activos.json"

ACCIONES_PERMITIDAS = {
    "crear_archivo",
    "validar_sintaxis",
    "activar_plugin",
    "probar_plugin",
    "verificacion_manual",
    "probar_agent_loop",
    "rebuild_docker"
}


def ruta_segura_plugin(ruta):
    ruta_norm = os.path.normpath(ruta)

    if not ruta_norm.startswith("plugins/"):
        return False

    if ".." in ruta_norm:
        return False

    if not ruta_norm.endswith(".py"):
        return False

    return True


def ejecutar_comando_seguro(comando: str) -> dict:
    bloqueados = ["rm ", "sudo", "shutdown", "reboot", "mkfs", "chmod 777 /"]

    for peligroso in bloqueados:
        if peligroso in comando:
            return {
                "ok": False,
                "error": f"Comando bloqueado por seguridad: {peligroso}"
            }

    try:
        resultado = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=25
        )

        return {
            "ok": resultado.returncode == 0,
            "returncode": resultado.returncode,
            "stdout": resultado.stdout.strip(),
            "stderr": resultado.stderr.strip()
        }

    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }


def crear_archivo_plugin(tarea):
    archivo = tarea.get("archivo")

    if not archivo:
        return False, "No se indicó archivo."

    if not ruta_segura_plugin(archivo):
        return False, "Ruta no permitida. Solo se permite crear archivos .py dentro de plugins/."

    nombre_plugin = os.path.basename(archivo).replace(".py", "")

    contenido = f'''"""
Plugin generado por Executor V2.
Nombre: {nombre_plugin}
"""

def run(params):
    return "Plugin {nombre_plugin} creado correctamente. Pendiente implementar lógica real."
'''

    os.makedirs(PLUGINS_DIR, exist_ok=True)

    if os.path.exists(archivo):
        return True, f"El archivo {archivo} ya existe. No se sobrescribió."

    with open(archivo, "w", encoding="utf-8") as f:
        f.write(contenido)

    return True, f"Archivo creado: {archivo}"


def activar_plugin(tarea):
    plugin = tarea.get("plugin")

    if not plugin:
        return False, "No se indicó nombre del plugin."

    if "/" in plugin or ".." in plugin or plugin.endswith(".py"):
        return False, "Nombre de plugin inválido."

    data = {"activos": []}

    if os.path.exists(PLUGINS_ACTIVOS):
        with open(PLUGINS_ACTIVOS, "r", encoding="utf-8") as f:
            data = json.load(f)

    activos = data.get("activos", [])

    if plugin not in activos:
        activos.append(plugin)

    data["activos"] = activos

    with open(PLUGINS_ACTIVOS, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return True, f"Plugin activado en plugins_activos.json: {plugin}"


def ejecutar_tarea(tarea: dict) -> dict:
    accion = tarea.get("accion")
    resultado = dict(tarea)

    if accion not in ACCIONES_PERMITIDAS:
        resultado["estado"] = "NO_EJECUTADA"
        resultado["resultado"] = "Acción no permitida."
        return resultado

    if accion == "crear_archivo":
        ok, mensaje = crear_archivo_plugin(tarea)
        resultado["estado"] = "COMPLETADO" if ok else "FALLIDO"
        resultado["resultado"] = mensaje
        return resultado

    if accion == "activar_plugin":
        ok, mensaje = activar_plugin(tarea)
        resultado["estado"] = "COMPLETADO" if ok else "FALLIDO"
        resultado["resultado"] = mensaje
        return resultado

    if accion == "verificacion_manual":
        resultado["estado"] = "PENDIENTE_MANUAL"
        resultado["resultado"] = "Requiere revisión manual."
        return resultado

    if accion == "probar_agent_loop":
        resultado["estado"] = "PENDIENTE_MANUAL"
        resultado["resultado"] = "Prueba interactiva con agent_loop.py requiere ejecución manual."
        return resultado

    if accion == "rebuild_docker":
        resultado["estado"] = "PENDIENTE_MANUAL"
        resultado["resultado"] = "Rebuild Docker requiere confirmación manual."
        return resultado

    comando = tarea.get("comando")

    if accion in ("validar_sintaxis", "probar_plugin"):
        salida = ejecutar_comando_seguro(comando)

        if salida.get("ok"):
            resultado["estado"] = "COMPLETADO"
            resultado["resultado"] = salida.get("stdout") or "PASS"
        else:
            resultado["estado"] = "FALLIDO"
            resultado["resultado"] = salida.get("stderr") or salida.get("error") or "Error desconocido"

        resultado["detalle_ejecucion"] = salida
        return resultado

    resultado["estado"] = "NO_EJECUTADA"
    resultado["resultado"] = "Acción no implementada."
    return resultado


def ejecutar_plan(objetivo: str) -> dict:
    descompuesto = descomponer_tareas(objetivo)

    if not descompuesto.get("ok"):
        return {
            "ok": False,
            "error": descompuesto.get("error", "No se pudo descomponer el objetivo."),
            "objetivo": objetivo
        }

    tareas = descompuesto.get("tareas", [])
    resultados = []

    for tarea in tareas:
        resultado = ejecutar_tarea(tarea)
        resultados.append(resultado)

    if any(t.get("estado") == "FALLIDO" for t in resultados):
        estado_final = "FALLIDO"
    elif any(t.get("estado") in ("NO_EJECUTADA", "PENDIENTE_MANUAL") for t in resultados):
        estado_final = "PARCIAL"
    else:
        estado_final = "COMPLETADO"

    return {
        "ok": estado_final != "FALLIDO",
        "version": "EXECUTOR_V2",
        "objetivo": objetivo,
        "estado_final": estado_final,
        "resultados": resultados
    }


if __name__ == "__main__":
    objetivo = input("Objetivo para ejecutar: ").strip()
    salida = ejecutar_plan(objetivo)
    print(json.dumps(salida, indent=2, ensure_ascii=False))
