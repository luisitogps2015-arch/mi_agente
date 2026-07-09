from agents.base_agent import BaseAgent


class SelfHealingAgent(BaseAgent):

    def __init__(self):
        super().__init__("SelfHealingAgent")

    def run(self, reflection_result):

        estado = "SELF_HEALING_COMPLETED"

        self.remember(
            task="SELF_HEALING",
            result=estado
        )

        return {
            "agent": self.name,
            "decision": estado,
            "result": {
                "ok": True,
                "accion": (
                    "No se requiere corrección "
                    "automática por el momento."
                ),
                "reflection_result": reflection_result
            }
        }


if __name__ == "__main__":

    agent = SelfHealingAgent()

    salida = agent.run(
        {
            "ok": True,
            "reflexion": "Resultado evaluado"
        }
    )

    print(salida)
