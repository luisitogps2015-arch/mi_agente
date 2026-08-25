"""Prueba real opt-in del flujo API -> Flask -> CrewAI."""

import json
import os
import time

from app import app


def main() -> None:
    client = app.test_client()
    token = os.getenv("CREW_DASHBOARD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("CREW_DASHBOARD_TOKEN es obligatorio para el smoke real.")
    headers = {"Authorization": f"Bearer {token}"}
    ingestion_response = client.post(
        "/api/ingestion/api",
        json={"source": "jsonplaceholder_todo"},
        headers=headers,
    )
    if ingestion_response.status_code != 200:
        raise RuntimeError(f"Ingestion falló: {ingestion_response.get_json()}")
    ingestion = ingestion_response.get_json()

    run_response = client.post(
        "/api/crew/run",
        json={
            "topic": (
                "Analiza este registro TODO. Conserva y menciona los valores "
                "exactos de id, userId, title y completed en cada etapa."
            ),
            "source_type": "api",
            "ingestion_id": ingestion["ingestion_id"],
        },
        headers=headers,
    )
    if run_response.status_code != 202:
        raise RuntimeError(f"Crew run falló: {run_response.get_json()}")

    started = run_response.get_json()
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        run = client.get(started["status_url"], headers=headers).get_json()
        if run["status"] in {"DONE", "ERROR"}:
            break
        time.sleep(1)
    else:
        raise RuntimeError("La Crew no terminó dentro de 240 segundos.")

    if run["status"] != "DONE":
        raise RuntimeError(f"La Crew terminó con error: {run.get('error')}")

    exact_title = "delectus aut autem"
    outputs = {
        "research": run.get("research_output", ""),
        "analysis": run.get("analysis_output", ""),
        "validation": run.get("validation_output", ""),
    }
    references = {key: exact_title.lower() in value.lower() for key, value in outputs.items()}
    if not all(references.values()):
        raise RuntimeError(f"Algún output no referencia el title real: {references}")

    print(json.dumps({
        "ingestion": ingestion,
        "run_id": run["run_id"],
        "source_type": run["source_type"],
        "source_name": run["source_name"],
        "references_real_title": references,
        "research_output": outputs["research"],
        "analysis_output": outputs["analysis"],
        "validation_output": outputs["validation"],
        "validation_status": run["validation_status"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
