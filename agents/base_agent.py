import json
import os
from datetime import datetime, timezone


class BaseAgent:

    def __init__(self, name):
        self.name = name
        self.state_file = f"agents/state/{name}.json"

        self._crear_estado()

    def _crear_estado(self):
        if not os.path.exists(self.state_file):

            estado = {
                "name": self.name,
                "runs": 0,
                "last_task": "",
                "last_result": "",
                "updated": self._ahora()
            }

            self._guardar(estado)

    def _ahora(self):
        return datetime.now(timezone.utc).isoformat()

    def _cargar(self):
        with open(
            self.state_file,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    def _guardar(self, estado):
        with open(
            self.state_file,
            "w",
            encoding="utf-8"
        ) as f:
            json.dump(
                estado,
                f,
                indent=2,
                ensure_ascii=False
            )

    def remember(self, task, result):

        estado = self._cargar()

        estado["runs"] += 1
        estado["last_task"] = task
        estado["last_result"] = str(result)
        estado["updated"] = self._ahora()

        self._guardar(estado)

    def state(self):
        return self._cargar()
