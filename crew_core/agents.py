"""Factories de los Agents base de CrewAI."""

from crewai import Agent

from .llm import create_llm


def create_researcher() -> Agent:
    """Crea el Agent responsable de recopilar y organizar información."""
    return Agent(
        role="Researcher",
        goal=(
            "Investigar y organizar la información necesaria para responder "
            "al objetivo recibido, identificando hechos, contexto y elementos "
            "relevantes sin inventar información no disponible."
        ),
        backstory=(
            "Especialista en recopilación y organización de información. "
            "Su responsabilidad es producir una base clara y estructurada "
            "para que otro agente pueda analizarla."
        ),
        llm=create_llm(),
        allow_delegation=False,
        tools=[],
        memory=False,
    )


def create_analyst() -> Agent:
    """Crea el Agent responsable de analizar la evidencia organizada."""
    return Agent(
        role="Analyst",
        goal=(
            "Analizar de forma lógica y estructurada la información recibida "
            "del Researcher, identificar patrones, relaciones y conclusiones "
            "relevantes."
        ),
        backstory=(
            "Especialista en análisis. Trabaja sobre la evidencia y contexto "
            "proporcionados y transforma información organizada en hallazgos "
            "y conclusiones comprensibles."
        ),
        llm=create_llm(),
        allow_delegation=False,
        tools=[],
        memory=False,
    )


def create_validator() -> Agent:
    """Crea el Agent responsable del control de calidad del análisis."""
    return Agent(
        role="Validator",
        goal=(
            "Revisar el análisis producido, detectar inconsistencias, "
            "contradicciones, afirmaciones no sustentadas u omisiones "
            "importantes y determinar si el resultado es suficientemente "
            "coherente y completo."
        ),
        backstory=(
            "Especialista en control de calidad de resultados de IA. "
            "Su función es revisar críticamente el trabajo anterior antes "
            "de considerarlo resultado final."
        ),
        llm=create_llm(),
        allow_delegation=False,
        tools=[],
        memory=False,
    )
