from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

from plugins.procesar_documento_pm import run as procesar_documento


class PMState(TypedDict, total=False):
    entrada: str
    proyecto_id: str
    tipo: str
    resultado_intake: dict
    resultado_pm: dict
    estado: str
    error: str


def intake_agent(state: PMState) -> PMState:
    state["estado"] = "INTAKE_COMPLETED"
    return state


def document_agent(state: PMState) -> PMState:
    ruta = state.get("entrada", "")
    proyecto_id = state.get("proyecto_id", "proyecto_001")

    resultado = procesar_documento({
        "proyecto_id": proyecto_id,
        "ruta": ruta,
        "titulo": "Documento procesado por LangGraph PM Copilot"
    })

    state["resultado_pm"] = resultado

    if not resultado.get("ok"):
        state["estado"] = "ERROR"
        state["error"] = resultado.get("error", "Error procesando documento")
    else:
        state["estado"] = "DOCUMENT_PROCESSED"

    return state


def critic_agent(state: PMState) -> PMState:
    resultado = state.get("resultado_pm", {})

    if not resultado.get("ok"):
        state["estado"] = "CRITIC_FAILED"
        return state

    caracteres = resultado.get("caracteres_extraidos", 0)

    if caracteres < 50:
        state["estado"] = "LOW_CONFIDENCE"
        state["error"] = "Texto extraído insuficiente para generar artefactos confiables."
    else:
        state["estado"] = "CRITIC_APPROVED"

    return state


def delivery_agent(state: PMState) -> PMState:
    if state.get("error"):
        state["estado"] = "DELIVERY_WITH_ERROR"
    else:
        state["estado"] = "DELIVERY_COMPLETED"

    return state


def debe_continuar(state: PMState) -> str:
    if state.get("estado") == "ERROR":
        return "delivery_agent"
    return "critic_agent"


workflow = StateGraph(PMState)

workflow.add_node("intake_agent", intake_agent)
workflow.add_node("document_agent", document_agent)
workflow.add_node("critic_agent", critic_agent)
workflow.add_node("delivery_agent", delivery_agent)

workflow.add_edge(START, "intake_agent")
workflow.add_edge("intake_agent", "document_agent")
workflow.add_conditional_edges(
    "document_agent",
    debe_continuar,
    {
        "critic_agent": "critic_agent",
        "delivery_agent": "delivery_agent"
    }
)
workflow.add_edge("critic_agent", "delivery_agent")
workflow.add_edge("delivery_agent", END)

graph = workflow.compile()


def ejecutar_pm_graph(ruta_documento: str, proyecto_id: str = "proyecto_001"):
    estado_inicial = {
        "entrada": ruta_documento,
        "proyecto_id": proyecto_id,
        "tipo": "documento",
        "estado": "STARTED"
    }

    return graph.invoke(estado_inicial)
