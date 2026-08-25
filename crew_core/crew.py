"""Ensamblado de la Crew secuencial de investigación."""

from crewai import Crew, Process

from .agents import create_analyst, create_researcher, create_validator
from .tasks import (
    create_analysis_task,
    create_research_task,
    create_validation_task,
)


def create_research_crew() -> Crew:
    """Crea la Crew de investigación sin iniciar su ejecución."""
    researcher = create_researcher()
    analyst = create_analyst()
    validator = create_validator()

    research_task = create_research_task(researcher)
    analysis_task = create_analysis_task(analyst, research_task)
    validation_task = create_validation_task(
        validator,
        research_task,
        analysis_task,
    )

    return Crew(
        agents=[researcher, analyst, validator],
        tasks=[research_task, analysis_task, validation_task],
        process=Process.sequential,
        verbose=False,
    )
