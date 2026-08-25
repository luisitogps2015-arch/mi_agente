"""Factories de las Tasks y sus handoffs nativos de CrewAI."""

from crewai import Agent, Task
from crewai.tasks.task_output import TaskOutput


VALIDATION_STATUSES = {
    "VALIDATION_STATUS: APPROVED",
    "VALIDATION_STATUS: NEEDS_REVISION",
}


def validate_validation_status(output: TaskOutput) -> tuple[bool, str]:
    """Valida que la última línea contenga un estado permitido exacto."""
    lines = output.raw.splitlines()
    if lines and lines[-1] in VALIDATION_STATUSES:
        return True, output.raw

    return (
        False,
        "La última línea debe ser exactamente "
        "'VALIDATION_STATUS: APPROVED' o "
        "'VALIDATION_STATUS: NEEDS_REVISION'.",
    )


def create_research_task(researcher: Agent) -> Task:
    """Crea la investigación inicial sin contexto de Tasks anteriores."""
    return Task(
        description=(
            "Objetivo/topic: {topic}.\n\n"
            "Datos proporcionados:\n{input_data}\n\n"
            "Instrucción de datos: {data_instructions}\n\n"
            "Investigar y organizar el objetivo recibido. "
            "Generar una base estructurada para el Analyst trabajando únicamente "
            "con el contexto disponible. No inventar fuentes ni valores. Identificar "
            "la información faltante y las incertidumbres, y separar los datos o "
            "hechos de las inferencias."
        ),
        expected_output=(
            "Un research brief estructurado que incluya, como mínimo:\n"
            "- tema investigado;\n"
            "- información relevante;\n"
            "- contexto;\n"
            "- puntos principales;\n"
            "- incertidumbres o limitaciones;\n"
            "- elementos que deberían analizarse posteriormente."
        ),
        agent=researcher,
        context=[],
        tools=[],
    )


def create_analysis_task(analyst: Agent, research_task: Task) -> Task:
    """Crea el análisis usando la investigación como contexto nativo."""
    return Task(
        description=(
            "Analizar el resultado producido por Research Task para el tema "
            "{topic}.\n\n"
            "Utilizar Research Task como base sin repetir la investigación desde "
            "cero. Identificar patrones, relaciones, implicaciones y conclusiones; "
            "distinguir evidencia de interpretación y señalar las limitaciones "
            "importantes."
        ),
        expected_output=(
            "Un análisis estructurado que incluya:\n"
            "- principales hallazgos;\n"
            "- relaciones o patrones encontrados;\n"
            "- implicaciones;\n"
            "- conclusiones;\n"
            "- limitaciones."
        ),
        agent=analyst,
        context=[research_task],
        tools=[],
    )


def create_validation_task(
    validator: Agent,
    research_task: Task,
    analysis_task: Task,
) -> Task:
    """Crea la validación usando investigación y análisis como contexto nativo."""
    return Task(
        description=(
            "Revisar críticamente el análisis producido para {topic} comparándolo "
            "contra la investigación previa. Los datos originales suministrados "
            "fueron:\n{input_data}\n\n"
            "Comprobar la coherencia, las contradicciones, las afirmaciones no "
            "respaldadas por Research Task o por los datos suministrados, las "
            "omisiones importantes, las conclusiones excesivas y la separación "
            "entre evidencia e inferencia. No afirmar que se verificó por cuenta "
            "propia la fuente externa. Incluir una auditoría de correspondencia "
            "que cite los valores exactos relevantes de los datos suministrados y "
            "confirme si Research y Analysis los conservaron sin contradicciones. "
            "La última línea de la respuesta debe ser exactamente "
            "VALIDATION_STATUS: APPROVED o "
            "VALIDATION_STATUS: NEEDS_REVISION."
        ),
        expected_output=(
            "Un informe de validación estructurado que incluya:\n"
            "- estado general: APPROVED / NEEDS_REVISION;\n"
            "- hallazgos de validación;\n"
            "- auditoría de correspondencia con los datos suministrados;\n"
            "- inconsistencias detectadas;\n"
            "- afirmaciones no sustentadas;\n"
            "- omisiones;\n"
            "- recomendaciones de corrección;\n"
            "- conclusión final;\n"
            "- como última línea exacta, sin texto posterior: "
            "VALIDATION_STATUS: APPROVED o "
            "VALIDATION_STATUS: NEEDS_REVISION."
        ),
        agent=validator,
        context=[research_task, analysis_task],
        tools=[],
        guardrail=validate_validation_status,
    )
