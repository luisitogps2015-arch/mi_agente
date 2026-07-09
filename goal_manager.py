import json
import os
import uuid
from datetime import datetime, timezone

GOALS_FILE = "goals.json"


def _ahora():
    return datetime.now(timezone.utc).isoformat()


def _crear_archivo_si_no_existe():
    if not os.path.exists(GOALS_FILE):
        with open(GOALS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2, ensure_ascii=False)


def cargar_goals():
    _crear_archivo_si_no_existe()

    try:
        with open(GOALS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def guardar_goals(goals):
    with open(GOALS_FILE, "w", encoding="utf-8") as f:
        json.dump(goals, f, indent=2, ensure_ascii=False)


def crear_objetivo(objetivo: str):
    goals = cargar_goals()

    goal = {
        "id": str(uuid.uuid4())[:8],
        "objetivo": objetivo,
        "estado": "PENDIENTE",
        "avance": 0,
        "creado": _ahora(),
        "actualizado": _ahora(),
        "proxima_accion": "Pendiente de planificación",
        "historial": []
    }

    goals.append(goal)
    guardar_goals(goals)

    return {
        "ok": True,
        "goal": goal
    }


def listar_objetivos(estado=None):
    goals = cargar_goals()

    if estado:
        goals = [
            g for g in goals
            if g.get("estado", "").upper() == estado.upper()
        ]

    return {
        "ok": True,
        "goals": goals
    }


def listar_pendientes():
    goals = cargar_goals()

    pendientes = [
        g for g in goals
        if g.get("estado") in ("PENDIENTE", "EN_PROGRESO", "PARCIAL", "FALLIDO")
    ]

    return {
        "ok": True,
        "goals": pendientes
    }


def obtener_objetivo(goal_id: str):
    goals = cargar_goals()

    for goal in goals:
        if goal.get("id") == goal_id:
            return {
                "ok": True,
                "goal": goal
            }

    return {
        "ok": False,
        "error": "Objetivo no encontrado."
    }


def eliminar_objetivo(goal_id: str):
    goals = cargar_goals()

    nuevos = [
        g for g in goals
        if g.get("id") != goal_id
    ]

    if len(nuevos) == len(goals):
        return {
            "ok": False,
            "error": "Objetivo no encontrado."
        }

    guardar_goals(nuevos)

    return {
        "ok": True,
        "id": goal_id,
        "mensaje": "Objetivo eliminado."
    }


def actualizar_objetivo(
    objetivo: str,
    estado: str,
    avance: int = None,
    proxima_accion: str = None
):
    goals = cargar_goals()

    actualizado = False

    for goal in goals:
        if goal.get("objetivo", "").lower() == objetivo.lower():
            goal["estado"] = estado
            goal["actualizado"] = _ahora()

            if avance is not None:
                goal["avance"] = max(0, min(100, int(avance)))

            if proxima_accion is not None:
                goal["proxima_accion"] = proxima_accion

            goal.setdefault("historial", []).append({
                "fecha": _ahora(),
                "estado": estado,
                "avance": goal.get("avance", 0),
                "proxima_accion": goal.get("proxima_accion", "")
            })

            actualizado = True
            break

    if actualizado:
        guardar_goals(goals)

    return {
        "ok": actualizado
    }


def actualizar_objetivo_por_id(
    goal_id: str,
    estado: str = None,
    avance: int = None,
    proxima_accion: str = None
):
    goals = cargar_goals()

    for goal in goals:
        if goal.get("id") == goal_id:
            if estado is not None:
                goal["estado"] = estado

            if avance is not None:
                goal["avance"] = max(0, min(100, int(avance)))

            if proxima_accion is not None:
                goal["proxima_accion"] = proxima_accion

            goal["actualizado"] = _ahora()

            goal.setdefault("historial", []).append({
                "fecha": _ahora(),
                "estado": goal.get("estado"),
                "avance": goal.get("avance"),
                "proxima_accion": goal.get("proxima_accion", "")
            })

            guardar_goals(goals)

            return {
                "ok": True,
                "goal": goal
            }

    return {
        "ok": False,
        "error": "Objetivo no encontrado."
    }


def calcular_avance_por_pasos(completados: int, total: int):
    if total <= 0:
        return 0

    return round((completados / total) * 100)


if __name__ == "__main__":
    print("1. Crear objetivo")
    print("2. Listar objetivos")
    print("3. Listar pendientes")
    print("4. Ver objetivo")
    print("5. Eliminar objetivo")
    print("6. Actualizar objetivo por ID")

    opcion = input("Opción: ").strip()

    if opcion == "1":
        objetivo = input("Objetivo: ").strip()
        salida = crear_objetivo(objetivo)

    elif opcion == "2":
        salida = listar_objetivos()

    elif opcion == "3":
        salida = listar_pendientes()

    elif opcion == "4":
        goal_id = input("ID: ").strip()
        salida = obtener_objetivo(goal_id)

    elif opcion == "5":
        goal_id = input("ID a eliminar: ").strip()
        salida = eliminar_objetivo(goal_id)

    elif opcion == "6":
        goal_id = input("ID: ").strip()
        estado = input("Estado: ").strip()
        avance = input("Avance 0-100: ").strip()
        proxima_accion = input("Próxima acción: ").strip()

        salida = actualizar_objetivo_por_id(
            goal_id=goal_id,
            estado=estado or None,
            avance=int(avance) if avance else None,
            proxima_accion=proxima_accion or None
        )

    else:
        salida = {
            "ok": False,
            "error": "Opción inválida."
        }

    print(json.dumps(salida, indent=2, ensure_ascii=False))
