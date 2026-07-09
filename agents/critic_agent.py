from agents.base_agent import BaseAgent


class CriticAgent(BaseAgent):

    def __init__(self):
        super().__init__("CriticAgent")

    def run(self, resultado_executor):

        estado = "EVALUADO"

        self.remember(
            task="CRITIC_REVIEW",
            result=estado
        )

        return {
            "agent": self.name,
            "decision": estado,
            "result": {
                "ok": True,
                "evaluacion": "Resultado recibido y evaluado",
                "executor_result": resultado_executor
            }
        }


if __name__ == "__main__":

    agent = CriticAgent()

    salida = agent.run(
        {
            "ok": True,
            "estado_final": "COMPLETADO"
        }
    )

    print(salida)
