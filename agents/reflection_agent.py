from agents.base_agent import BaseAgent


class ReflectionAgent(BaseAgent):

    def __init__(self):
        super().__init__("ReflectionAgent")

    def run(self, critic_result):

        estado = "REFLECTION_CREATED"

        self.remember(
            task="REFLECT_CRITIC_RESULT",
            result=estado
        )

        return {
            "agent": self.name,
            "decision": estado,
            "result": {
                "ok": True,
                "reflexion": "Resultado evaluado. Se genera reflexión operativa.",
                "critic_result": critic_result
            }
        }


if __name__ == "__main__":

    agent = ReflectionAgent()

    salida = agent.run(
        {
            "ok": True,
            "evaluacion": "Resultado recibido y evaluado"
        }
    )

    print(salida)
