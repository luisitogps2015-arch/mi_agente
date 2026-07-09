from task_decomposer import descomponer_tareas

def run(params):
    objetivo = params.get("objetivo") or params.get("query") or params.get("texto")

    if not objetivo:
        return "Error: falta parámetro objetivo."

    resultado = descomponer_tareas(objetivo)

    if not resultado.get("ok"):
        return f"Error: {resultado.get('error')}"

    tareas = resultado.get("tareas", [])

    salida = [f"Objetivo: {resultado.get('objetivo')}", ""]
    salida.append("Tareas generadas:")

    for t in tareas:
        salida.append(
            f"{t.get('orden')}. {t.get('tarea')} "
            f"[{t.get('accion')}] - Estado: {t.get('estado')}"
        )

    return "\n".join(salida)
