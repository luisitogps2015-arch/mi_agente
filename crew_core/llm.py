"""Configuración centralizada del LLM de CrewAI sobre Groq."""

from __future__ import annotations

import os
from typing import Any

from crewai.llms.base_llm import BaseLLM
from groq import Groq
from pydantic import Field


DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"
GROQ_MODEL_ENV = "CREWAI_GROQ_MODEL"


class GroqLLM(BaseLLM):
    """Adaptador mínimo del cliente Groq al contrato LLM de CrewAI 1.14.7."""

    llm_type: str = "groq"
    provider: str = "groq"
    api_key: str | None = Field(default=None, exclude=True, repr=False)

    def call(
        self,
        messages: str | list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        callbacks: list[Any] | None = None,
        available_functions: dict[str, Any] | None = None,
        from_task: Any = None,
        from_agent: Any = None,
        response_model: type[Any] | None = None,
    ) -> str:
        """Solicita una respuesta de texto a Groq cuando CrewAI ejecuta el LLM."""
        del callbacks, available_functions, from_task, from_agent

        if tools:
            raise ValueError("GroqLLM no tiene Tools habilitadas en esta fase.")
        if response_model is not None:
            raise ValueError("GroqLLM no admite salida estructurada en esta fase.")
        if not self.api_key:
            raise RuntimeError("GROQ_API_KEY no está configurada.")

        formatted_messages = self._format_messages(messages)
        request: dict[str, Any] = {
            "model": self.model,
            "messages": formatted_messages,
        }
        if self.temperature is not None:
            request["temperature"] = self.temperature
        if self.max_tokens is not None:
            request["max_tokens"] = int(self.max_tokens)
        if self.stop_sequences:
            request["stop"] = self.stop_sequences

        response = Groq(api_key=self.api_key).chat.completions.create(**request)
        content = response.choices[0].message.content or ""
        return self._apply_stop_words(content)


def create_llm() -> GroqLLM:
    """Crea el LLM configurado sin realizar llamadas al proveedor."""
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY no está configurada.")

    model = os.getenv(GROQ_MODEL_ENV, DEFAULT_GROQ_MODEL).strip()
    if not model:
        model = DEFAULT_GROQ_MODEL

    return GroqLLM(
        model=model,
        provider="groq",
        api_key=api_key,
        temperature=0.0,
    )
