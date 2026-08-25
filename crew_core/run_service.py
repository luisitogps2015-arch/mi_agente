"""Ejecución asíncrona y estado en memoria de runs CrewAI."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar
from copy import deepcopy
import json
import logging
import re
from threading import RLock
import time
from typing import Any
from uuid import uuid4

from crewai.events.event_bus import crewai_event_bus
from crewai.events.types.crew_events import (
    CrewKickoffCompletedEvent,
    CrewKickoffFailedEvent,
    CrewKickoffStartedEvent,
)
from crewai.events.types.task_events import (
    TaskCompletedEvent,
    TaskFailedEvent,
    TaskStartedEvent,
)

from .runner import run_research_crew


MAX_TOPIC_LENGTH = 4000
MAX_INPUT_DATA_BYTES = 128 * 1024
RUN_COOLDOWN_SECONDS = 15
RUN_RETENTION_SECONDS = 60 * 60
MAX_COMPLETED_RUNS = 50
_ACTIVE_STATUSES = {"RUNNING"}
_AGENT_KEYS = {
    "Researcher": "researcher",
    "Analyst": "analyst",
    "Validator": "validator",
}
_OUTPUT_KEYS = {
    "researcher": "research_output",
    "analyst": "analysis_output",
    "validator": "validation_output",
}
_VALIDATION_STATUS_RE = re.compile(
    r"^VALIDATION_STATUS: (APPROVED|NEEDS_REVISION)$"
)

_current_run_id: ContextVar[str | None] = ContextVar(
    "crew_run_id", default=None
)
log = logging.getLogger(__name__)


class CrewRunBusyError(RuntimeError):
    """Indica que el POC ya tiene una Crew activa."""


class CrewRunRateLimitError(RuntimeError):
    """Indica que aún no terminó el cooldown entre ejecuciones."""

    def __init__(self, retry_after: int) -> None:
        super().__init__("Espera antes de iniciar otra ejecución Crew.")
        self.retry_after = retry_after


class CrewRunRateLimiter:
    """Cooldown global y thread-safe para proteger el coste del POC."""

    def __init__(
        self,
        cooldown_seconds: int = RUN_COOLDOWN_SECONDS,
        clock: Any = time.monotonic,
    ) -> None:
        self._cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._lock = RLock()
        self._last_started_at: float | None = None

    def acquire(self) -> None:
        now = self._clock()
        with self._lock:
            if self._last_started_at is not None:
                remaining = self._cooldown_seconds - (now - self._last_started_at)
                if remaining > 0:
                    raise CrewRunRateLimitError(max(1, int(remaining + 0.999)))
            self._last_started_at = now


class CrewRunRegistry:
    """Registro thread-safe con un único worker para la Crew del POC."""

    def __init__(
        self,
        retention_seconds: int = RUN_RETENTION_SECONDS,
        max_completed_runs: int = MAX_COMPLETED_RUNS,
        clock: Any = time.monotonic,
    ) -> None:
        self._lock = RLock()
        self._runs: dict[str, dict[str, Any]] = {}
        self._retention_seconds = retention_seconds
        self._max_completed_runs = max_completed_runs
        self._clock = clock
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="crew-run")

    def start(
        self,
        topic: str,
        input_data: Any | None = None,
        source_type: str = "manual",
        source_name: str | None = None,
        rate_limiter: CrewRunRateLimiter | None = None,
    ) -> dict[str, Any]:
        with self._lock:
            self._purge_locked(self._clock())
            if any(run["status"] in _ACTIVE_STATUSES for run in self._runs.values()):
                raise CrewRunBusyError("Ya existe una ejecución Crew activa.")
            if rate_limiter is not None:
                rate_limiter.acquire()

            run_id = str(uuid4())
            self._runs[run_id] = {
                "run_id": run_id,
                "status": "RUNNING",
                "process": "sequential",
                "source_type": source_type,
                "source_name": source_name,
                "agents": {
                    "researcher": {"status": "WAITING"},
                    "analyst": {"status": "WAITING"},
                    "validator": {"status": "WAITING"},
                },
                "validation_status": None,
                "final_output": None,
                "error": None,
                "created_at": self._clock(),
                "finished_at": None,
            }
            snapshot = deepcopy(self._runs[run_id])
            self._executor.submit(self._execute, run_id, topic, input_data)
            return snapshot

    def get(self, run_id: str) -> dict[str, Any] | None:
        with self._lock:
            self._purge_locked(self._clock())
            run = self._runs.get(run_id)
            return deepcopy(run) if run is not None else None

    def has_active(self) -> bool:
        with self._lock:
            self._purge_locked(self._clock())
            return any(
                run["status"] in _ACTIVE_STATUSES for run in self._runs.values()
            )

    def task_started(self, run_id: str, role: str | None) -> None:
        key = _AGENT_KEYS.get(role or "")
        if not key:
            return
        with self._lock:
            agent = self._runs[run_id]["agents"][key]
            if agent["status"] == "WAITING":
                agent["status"] = "RUNNING"

    def task_completed(self, run_id: str, role: str | None, raw: str) -> None:
        key = _AGENT_KEYS.get(role or "")
        if not key:
            return
        with self._lock:
            run = self._runs[run_id]
            run["agents"][key]["status"] = "DONE"
            run[_OUTPUT_KEYS[key]] = raw

    def fail(self, run_id: str, role: str | None = None) -> None:
        with self._lock:
            run = self._runs.get(run_id)
            if not run:
                return
            key = _AGENT_KEYS.get(role or "")
            if key:
                run["agents"][key]["status"] = "ERROR"
                run["error"] = f"La tarea {role} falló."
            elif run["error"] is None:
                run["error"] = "La ejecución Crew falló."
            run["status"] = "ERROR"
            run["finished_at"] = self._clock()

    def _execute(self, run_id: str, topic: str, input_data: Any | None) -> None:
        token = _current_run_id.set(run_id)
        try:
            output = run_research_crew(topic, input_data=input_data)
            crewai_event_bus.flush()
            validation_status = self._extract_validation_status(output.raw)
            with self._lock:
                run = self._runs[run_id]
                for index, key in enumerate(("researcher", "analyst", "validator")):
                    task_output = output.tasks_output[index]
                    run["agents"][key]["status"] = "DONE"
                    run[_OUTPUT_KEYS[key]] = task_output.raw
                run["validation_status"] = validation_status
                run["final_output"] = output.raw
                run["status"] = "DONE"
                run["error"] = None
                run["finished_at"] = self._clock()
        except Exception as exc:
            log.exception(
                "Crew run %s falló internamente (%s).",
                run_id,
                type(exc).__name__,
            )
            self.fail(run_id)
        finally:
            _current_run_id.reset(token)

    @staticmethod
    def _extract_validation_status(raw: str) -> str | None:
        lines = raw.splitlines()
        if not lines:
            return None
        match = _VALIDATION_STATUS_RE.fullmatch(lines[-1])
        return match.group(1) if match else None

    def _purge_locked(self, now: float) -> None:
        completed = [
            (run_id, run)
            for run_id, run in self._runs.items()
            if run["status"] not in _ACTIVE_STATUSES
        ]
        for run_id, run in completed:
            finished_at = run.get("finished_at")
            if finished_at is not None and now - finished_at >= self._retention_seconds:
                del self._runs[run_id]

        remaining = [
            (run_id, run)
            for run_id, run in self._runs.items()
            if run["status"] not in _ACTIVE_STATUSES
        ]
        overflow = len(remaining) - self._max_completed_runs
        if overflow > 0:
            remaining.sort(key=lambda item: item[1].get("finished_at") or 0)
            for run_id, _ in remaining[:overflow]:
                del self._runs[run_id]


crew_run_registry = CrewRunRegistry()
crew_run_rate_limiter = CrewRunRateLimiter()


def validate_input_data(input_data: Any) -> Any:
    """Valida estructura y tamaño antes de enviarla a la Crew."""
    if not isinstance(input_data, (dict, list)):
        raise ValueError("input_data debe ser un objeto o array JSON.")
    try:
        encoded = json.dumps(input_data, ensure_ascii=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("input_data debe contener valores JSON válidos.") from exc
    if len(encoded) > MAX_INPUT_DATA_BYTES:
        raise ValueError(
            f"input_data excede el máximo de {MAX_INPUT_DATA_BYTES} bytes."
        )
    return input_data


def _event_run_id() -> str | None:
    return _current_run_id.get()


def _event_role(event: Any) -> str | None:
    task = getattr(event, "task", None)
    agent = getattr(task, "agent", None)
    return getattr(agent, "role", None) or getattr(event, "agent_role", None)


@crewai_event_bus.on(CrewKickoffStartedEvent)
def _on_crew_started(source: Any, event: CrewKickoffStartedEvent) -> None:
    del source, event


@crewai_event_bus.on(TaskStartedEvent)
def _on_task_started(source: Any, event: TaskStartedEvent) -> None:
    del source
    if run_id := _event_run_id():
        crew_run_registry.task_started(run_id, _event_role(event))


@crewai_event_bus.on(TaskCompletedEvent)
def _on_task_completed(source: Any, event: TaskCompletedEvent) -> None:
    del source
    if run_id := _event_run_id():
        crew_run_registry.task_completed(run_id, _event_role(event), event.output.raw)


@crewai_event_bus.on(TaskFailedEvent)
def _on_task_failed(source: Any, event: TaskFailedEvent) -> None:
    del source
    if run_id := _event_run_id():
        crew_run_registry.fail(run_id, _event_role(event))


@crewai_event_bus.on(CrewKickoffCompletedEvent)
def _on_crew_completed(source: Any, event: CrewKickoffCompletedEvent) -> None:
    del source, event


@crewai_event_bus.on(CrewKickoffFailedEvent)
def _on_crew_failed(source: Any, event: CrewKickoffFailedEvent) -> None:
    del source, event
    if run_id := _event_run_id():
        crew_run_registry.fail(run_id)
