import json
import os
from datetime import datetime, timezone
from uuid import uuid4


MEMORY_DIR = "memory"
EVENTS_FILE = os.path.join(MEMORY_DIR, "events.jsonl")
SUMMARY_FILE = os.path.join(MEMORY_DIR, "summary.json")


def asegurar_memoria():
    os.makedirs(MEMORY_DIR, exist_ok=True)

    if not os.path.exists(SUMMARY_FILE):
        resumen = {
            "total_eventos": 0,
            "por_tipo": {},
            "ultimos_eventos": []
        }

        with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
            json.dump(resumen, f, indent=2, ensure_ascii=False)


def ahora():
    return datetime.now(timezone.utc).isoformat()


def registrar_evento(tipo: str, objetivo: str, estado: str, data=None) -> dict:
    asegurar_memoria()

    evento = {
        "id": str(uuid4()),
        "fecha": ahora(),
        "tipo": tipo,
        "objetivo": objetivo,
        "estado": estado,
        "data": data or {}
    }

    with open(EVENTS_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")

    actualizar_resumen(evento)

    return {
        "ok": True,
        "evento": evento
    }


def actualizar_resumen(evento: dict):
    asegurar_memoria()

    with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
        resumen = json.load(f)

    resumen["total_eventos"] = resumen.get("total_eventos", 0) + 1

    tipo = evento.get("tipo", "desconocido")
    resumen["por_tipo"][tipo] = resumen["por_tipo"].get(tipo, 0) + 1

    ultimos = resumen.get("ultimos_eventos", [])
    ultimos.insert(0, {
        "id": evento.get("id"),
        "fecha": evento.get("fecha"),
        "tipo": evento.get("tipo"),
        "objetivo": evento.get("objetivo"),
        "estado": evento.get("estado")
    })

    resumen["ultimos_eventos"] = ultimos[:10]

    with open(SUMMARY_FILE, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)


def leer_resumen() -> dict:
    asegurar_memoria()

    with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
        resumen = json.load(f)

    return {
        "ok": True,
        "resumen": resumen
    }


def leer_eventos(limite=20) -> dict:
    asegurar_memoria()

    if not os.path.exists(EVENTS_FILE):
        return {
            "ok": True,
            "eventos": []
        }

    with open(EVENTS_FILE, "r", encoding="utf-8") as f:
        lineas = f.readlines()

    eventos = []

    for linea in lineas[-limite:]:
        try:
            eventos.append(json.loads(linea))
        except Exception:
            continue

    return {
        "ok": True,
        "eventos": eventos
    }


if __name__ == "__main__":
    print("1. Registrar evento de prueba")
    print("2. Ver resumen")
    print("3. Ver eventos")

    opcion = input("Opción: ").strip()

    if opcion == "1":
        salida = registrar_evento(
            tipo="test",
            objetivo="probar memoria",
            estado="COMPLETADO",
            data={"mensaje": "memoria funcionando"}
        )

    elif opcion == "2":
        salida = leer_resumen()

    elif opcion == "3":
        salida = leer_eventos()

    else:
        salida = {"ok": False, "error": "Opción inválida"}

    print(json.dumps(salida, indent=2, ensure_ascii=False))

