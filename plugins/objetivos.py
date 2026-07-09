from goal_manager import (
    crear_objetivo,
    listar_objetivos,
    listar_pendientes,
    obtener_objetivo,
    eliminar_objetivo,
    actualizar_objetivo_por_id
)


def formatear_goal(goal):
    return (
        f"- {goal.get('id')} | {goal.get('estado')} | "
        f"{goal.get('avance')}% | {goal.get('objetivo')} | "
        f"Próxima: {goal.get('proxima_accion', '')}"
    )


def run(params):
    modo = params.get("modo", "listar")

    if modo == "crear":
        objetivo = params.get("objetivo") or params.get("texto") or params.get("query")

        if not objetivo:
            return "Error: falta el objetivo."

        resultado = crear_objetivo(objetivo)

        if not resultado.get("ok"):
            return "Error creando objetivo."

        goal = resultado.get("goal", {})

        return (
            "Objetivo creado:\n"
            f"ID: {goal.get('id')}\n"
            f"Objetivo: {goal.get('objetivo')}\n"
            f"Estado: {goal.get('estado')}\n"
            f"Avance: {goal.get('avance')}%\n"
            f"Próxima acción: {goal.get('proxima_accion')}"
        )

    if modo == "listar":
        resultado = listar_objetivos()

        if not resultado.get("ok"):
            return "Error listando objetivos."

        goals = resultado.get("goals", [])

        if not goals:
            return "No hay objetivos registrados."

        salida = ["Objetivos registrados:"]
        salida.extend([formatear_goal(g) for g in goals])

        return "\n".join(salida)

    if modo == "pendientes":
        resultado = listar_pendientes()

        if not resultado.get("ok"):
            return "Error listando objetivos pendientes."

        goals = resultado.get("goals", [])

        if not goals:
            return "No hay objetivos pendientes."

        salida = ["Objetivos pendientes:"]
        salida.extend([formatear_goal(g) for g in goals])

        return "\n".join(salida)

    if modo == "ver":
        goal_id = params.get("id") or params.get("goal_id")

        if not goal_id:
            return "Error: falta id del objetivo."

        resultado = obtener_objetivo(goal_id)

        if not resultado.get("ok"):
            return resultado.get("error", "Objetivo no encontrado.")

        goal = resultado.get("goal", {})

        historial = goal.get("historial", [])

        salida = [
            "Detalle del objetivo:",
            f"ID: {goal.get('id')}",
            f"Objetivo: {goal.get('objetivo')}",
            f"Estado: {goal.get('estado')}",
            f"Avance: {goal.get('avance')}%",
            f"Próxima acción: {goal.get('proxima_accion')}",
            "",
            "Historial:"
        ]

        if historial:
            for h in historial[-5:]:
                salida.append(
                    f"- {h.get('fecha')} | {h.get('estado')} | "
                    f"{h.get('avance')}% | {h.get('proxima_accion')}"
                )
        else:
            salida.append("- Sin historial.")

        return "\n".join(salida)

    if modo == "eliminar":
        goal_id = params.get("id") or params.get("goal_id")

        if not goal_id:
            return "Error: falta id del objetivo."

        resultado = eliminar_objetivo(goal_id)

        if not resultado.get("ok"):
            return resultado.get("error", "No se pudo eliminar.")

        return f"Objetivo eliminado: {goal_id}"

    if modo == "actualizar":
        goal_id = params.get("id") or params.get("goal_id")

        if not goal_id:
            return "Error: falta id del objetivo."

        estado = params.get("estado")
        avance = params.get("avance")
        proxima_accion = params.get("proxima_accion")

        resultado = actualizar_objetivo_por_id(
            goal_id=goal_id,
            estado=estado,
            avance=avance,
            proxima_accion=proxima_accion
        )

        if not resultado.get("ok"):
            return resultado.get("error", "No se pudo actualizar.")

        goal = resultado.get("goal", {})

        return (
            "Objetivo actualizado:\n"
            f"ID: {goal.get('id')}\n"
            f"Estado: {goal.get('estado')}\n"
            f"Avance: {goal.get('avance')}%\n"
            f"Próxima acción: {goal.get('proxima_accion')}"
        )

    return "Error: modo no soportado."

