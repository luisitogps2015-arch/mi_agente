"""Punto de entrada para ejecutar la Crew de investigación."""

from __future__ import annotations

import json
from typing import Any

from crewai.crews.crew_output import CrewOutput

from .crew import create_research_crew


def run_research_crew(topic: str, input_data: Any | None = None) -> CrewOutput:
    """Ejecuta la Crew; ``input_data`` es opcional por compatibilidad."""
    if not isinstance(topic, str):
        raise TypeError("topic debe ser un string no vacío.")
    if not topic.strip():
        raise ValueError("topic no puede estar vacío ni contener solo espacios.")

    has_input_data = input_data is not None
    input_context = (
        json.dumps(input_data, ensure_ascii=False, indent=2, sort_keys=True)
        if has_input_data
        else "No se proporcionaron datos externos; trabajar solo con el tema."
    )

    crew = create_research_crew()
    return crew.kickoff(inputs={
        "topic": topic,
        "input_data": input_context,
        "data_instructions": (
            "Usar los datos proporcionados como fuente primaria. No inventar "
            "valores ausentes y señalar explícitamente la información faltante."
            if has_input_data
            else "No afirmar que se consultó o verificó una fuente externa."
        ),
    })
