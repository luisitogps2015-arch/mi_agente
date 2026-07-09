import json

from planner_engine import crear_plan
from task_decomposer import extraer_json
from executor_engine import ejecutar_tarea
from self_healing_engine import escribir_plugin_leer_logs, ejecutar_comando
from memory_manager import registrar_evento


def descomponer_desde_plan(objetivo: str, plan_texto: str) -> dict:
    """
    Descomposición ligera sin volver a llamar Planner/RAG.
    Para V2 evitamos llamadas repetidas a Groq.
    """
    objetivo_lower = objetivo.lower()

    if "leer logs" in objetivo_lower or "leer_logs" in objetivo_lower:
        tareas = [
            {
                "orden": 1,
                "tarea": "Crear archivo leer_logs.py",
                "accion": "crear_archivo",
                "archivo": "plugins/leer_logs.py",
                "estado": "pendiente"
            },
            {
                "orden": 2,
                "tarea": "Validar sintaxis de leer_logs.py",
                "accion": "validar_sintaxis",
                "archivo": "plugins/leer_logs.py",
                "comando": "python3 -m py_compile plugins/leer_logs.py",
                "estado": "pendiente"
            },
            {
                "orden": 3,
                "tarea": "Activar plugin leer_logs",
                "accion": "activar_plugin",
                "archivo": "plugins_activos.json",
                "plugin": "leer_logs",
                "estado": "pendiente"
            },
            {
                "orden": 4,
                "tarea": "Probar plugin leer_logs directo",
                "accion": "probar_plugin",
                "plugin": "leer_logs",
                "comando": "python3 -c \"from plugin_registry import run_plugin; print(run_plugin('leer_logs', {}))\"",
                "estado": "pendiente"
            },
            {
                "orden": 5,
                "tarea": "Probar flujo completo con agent_loop.py",
                "accion": "probar_agent_loop",
                "estado": "pendiente"
            },
            {
                "orden": 6,
                "tarea": "Rebuild Docker si se probará desde Telegram",
                "accion": "rebuild_docker",
                "estado": "pendiente"
            }
        ]

        return {
            "ok": True,
            "version": "TASK_DECOMPOSER_CACHEADO_V2",
            "objetivo": objetivo,
            "tareas": tareas,
            "plan_base": plan_texto
        }

    return {
        "ok": False,
        "error": "Orchestrator V2 solo tiene descomposición cacheada para leer_logs.",
        "objetivo": objetivo,
        "plan_base": plan_texto
    }


def ejecutar_tareas_cacheadas(tareas: list) -> dict:
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
        "version": "EXECUTOR_CACHEADO_V2",
        "estado_final": estado_final,
        "resultados": resultados
    }


def criticar_ejecucion_cacheada(objetivo: str, ejecucion: dict) -> dict:
    resultados = ejecucion.get("resultados", [])
    texto_resultados = json.dumps(resultados, ensure_ascii=False)

    cumple_parcial = False
    no_cumple = False
    problema = ""

    if "Pendiente implementar lógica real" in texto_resultados:
        cumple_parcial = True
        problema = "El plugin existe y se ejecuta, pero todavía no implementa lógica real."

    if ejecucion.get("estado_final") == "FALLIDO":
        no_cumple = True
        problema = "La ejecución falló en una o más tareas."

    if no_cumple:
        veredicto = "NO_CUMPLE"
    elif cumple_parcial or ejecucion.get("estado_final") == "PARCIAL":
        veredicto = "CUMPLE_PARCIALMENTE"
    else:
        veredicto = "CUMPLE"

    evaluacion = (
        f"Veredicto: {veredicto}\n\n"
        f"Evidencia: estado del executor = {ejecucion.get('estado_final')}.\n"
        f"Problema principal: {problema or 'No se detectó problema principal.'}\n"
        f"Recomendación: "
    )

    if veredicto == "CUMPLE_PARCIALMENTE":
        evaluacion += "Aplicar Self-Healing para completar la lógica real del plugin."
    elif veredicto == "NO_CUMPLE":
        evaluacion += "Revisar errores de ejecución antes de continuar."
    else:
        evaluacion += "No se requiere acción correctiva."

    return {
        "ok": True,
        "version": "CRITIC_CACHEADO_V2",
        "objetivo": objetivo,
        "veredicto": veredicto,
        "evaluacion": evaluacion,
        "ejecucion": ejecucion
    }


def reflexionar_cacheado(objetivo: str, critica: dict) -> dict:
    veredicto = critica.get("veredicto")

    if veredicto == "CUMPLE":
        candidato = "NO"
        accion = "Mantener resultado y registrar evento."
        fallo = "No se detectó fallo funcional."
    elif veredicto == "CUMPLE_PARCIALMENTE":
        candidato = "SI"
        accion = "Aplicar autocuración sobre el plugin leer_logs.py."
        fallo = "El plugin fue creado pero falta lógica real."
    else:
        candidato = "SI"
        accion = "Revisar errores y proponer corrección."
        fallo = "La ejecución falló."

    reflexion = (
        "1. Qué salió bien\n"
        "- El pipeline logró ejecutar las etapas disponibles.\n\n"
        "2. Qué falló o quedó incompleto\n"
        f"- {fallo}\n\n"
        "3. Aprendizaje\n"
        "- Crear un plugin no significa que cumpla funcionalmente el objetivo; debe probarse su lógica real.\n\n"
        "4. Próxima acción recomendada\n"
        f"- {accion}\n\n"
        "5. Candidato para Self-Healing\n"
        f"- {candidato}"
    )

    return {
        "ok": True,
        "version": "REFLECTION_CACHEADA_V2",
        "objetivo": objetivo,
        "reflexion": reflexion,
        "candidato_self_healing": candidato,
        "critica": critica
    }


def autocurar_rapido_cacheado(objetivo: str, reflexion: dict) -> dict:
    if reflexion.get("candidato_self_healing") != "SI":
        return {
            "ok": False,
            "mensaje": "No se requiere autocuración.",
            "estado_final": "NO_APLICADO"
        }

    if "leer logs" not in objetivo.lower() and "leer_logs" not in objetivo.lower():
        return {
            "ok": False,
            "mensaje": "Self-Healing V2 rápido solo soporta leer_logs.",
            "estado_final": "NO_APLICADO"
        }

    pasos = []

    ok, msg = escribir_plugin_leer_logs()
    pasos.append({
        "paso": 1,
        "accion": "actualizar_plugin",
        "estado": "COMPLETADO" if ok else "FALLIDO",
        "resultado": msg
    })

    validar = ejecutar_comando("python3 -m py_compile plugins/leer_logs.py")
    pasos.append({
        "paso": 2,
        "accion": "validar_sintaxis",
        "estado": "COMPLETADO" if validar.get("ok") else "FALLIDO",
        "resultado": validar
    })

    probar = ejecutar_comando(
        "python3 -c \"from plugin_registry import run_plugin; print(run_plugin('leer_logs', {'archivo':'app.log','lineas':5}))\""
    )
    pasos.append({
        "paso": 3,
        "accion": "probar_plugin",
        "estado": "COMPLETADO" if probar.get("ok") else "FALLIDO",
        "resultado": probar
    })

    estado_final = "COMPLETADO"

    if any(p.get("estado") == "FALLIDO" for p in pasos):
        estado_final = "FALLIDO"

    return {
        "ok": estado_final == "COMPLETADO",
        "version": "SELF_HEALING_CACHEADO_V2",
        "objetivo": objetivo,
        "estado_final": estado_final,
        "pasos": pasos
    }


def orquestar(objetivo: str) -> dict:
    resultado = {
        "ok": False,
        "version": "ORCHESTRATOR_V2_CACHEADO",
        "objetivo": objetivo,
        "pipeline": {}
    }

    plan = crear_plan(objetivo)
    resultado["pipeline"]["planner"] = plan

    if not plan.get("ok"):
        resultado["estado_final"] = "FALLIDO"
        resultado["error"] = plan.get("error")
        return resultado

    plan_texto = plan.get("plan", "")

    tareas = descomponer_desde_plan(objetivo, plan_texto)
    resultado["pipeline"]["task_decomposer"] = tareas

    if not tareas.get("ok"):
        resultado["estado_final"] = "FALLIDO"
        resultado["error"] = tareas.get("error")
        return resultado

    ejecucion = ejecutar_tareas_cacheadas(tareas.get("tareas", []))
    resultado["pipeline"]["executor"] = ejecucion

    critica = criticar_ejecucion_cacheada(objetivo, ejecucion)
    resultado["pipeline"]["critic"] = critica

    reflexion = reflexionar_cacheado(objetivo, critica)
    resultado["pipeline"]["reflection"] = reflexion

    autocura = autocurar_rapido_cacheado(objetivo, reflexion)
    resultado["pipeline"]["self_healing"] = autocura

    if autocura.get("ok"):
        estado_final = "COMPLETADO"
    else:
        estado_final = ejecucion.get("estado_final", "DESCONOCIDO")

    resultado["estado_final"] = estado_final
    resultado["ok"] = estado_final in ("COMPLETADO", "PARCIAL")

    registrar_evento(
        tipo="orchestrator",
        objetivo=objetivo,
        estado=estado_final,
        data={
            "version": resultado.get("version"),
            "planner_ok": plan.get("ok"),
            "task_decomposer_ok": tareas.get("ok"),
            "executor_estado": ejecucion.get("estado_final"),
            "critic_veredicto": critica.get("veredicto"),
            "reflection_self_healing": reflexion.get("candidato_self_healing"),
            "self_healing_ok": autocura.get("ok")
        }
    )

    return resultado


def resumen_orquestacion(data: dict) -> str:
    pipeline = data.get("pipeline", {})

    planner = pipeline.get("planner", {})
    task_decomposer = pipeline.get("task_decomposer", {})
    executor = pipeline.get("executor", {})
    critic = pipeline.get("critic", {})
    reflection = pipeline.get("reflection", {})
    self_healing = pipeline.get("self_healing", {})

    salida = [
        f"ORCHESTRATOR {data.get('version')}",
        f"Objetivo: {data.get('objetivo')}",
        f"Estado final: {data.get('estado_final')}",
        "",
        "Pipeline:",
        f"- Planner: {'OK' if planner.get('ok') else 'ERROR'}",
        f"- Task Decomposer: {'OK' if task_decomposer.get('ok') else 'ERROR'}",
        f"- Executor: {executor.get('estado_final')}",
        f"- Critic: {critic.get('veredicto')}",
        f"- Reflection Self-Healing: {reflection.get('candidato_self_healing')}",
        f"- Self-Healing: {'OK' if self_healing.get('ok') else self_healing.get('estado_final')}",
        "",
        "Resultado:"
    ]

    if self_healing.get("ok"):
        salida.append("Autocuración aplicada correctamente.")
    else:
        salida.append("No se aplicó autocuración o no fue necesaria.")

    return "\n".join(salida)


if __name__ == "__main__":
    objetivo = input("Objetivo para orquestar: ").strip()
    salida = orquestar(objetivo)

    print(json.dumps(salida, indent=2, ensure_ascii=False))
    print("\n" + "=" * 50 + "\n")
    print(resumen_orquestacion(salida))
