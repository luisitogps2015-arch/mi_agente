from agents.base_agent import BaseAgent


class ExecutorAgent(BaseAgent):

    def __init__(self):
        super().__init__("ExecutorAgent")

    def run(self, plan):

        estado = "PLAN_RECIBIDO"

        self.remember(
            task="EXECUTE_PLAN",
            result=estado
        )

        return {
            "agent": self.name,
            "decision": estado,
            "result": {
                "ok": True,
                "plan_recibido": True,
                "plan": plan
            }
        }


if __name__ == "__main__":

    agent = ExecutorAgent()

    salida = agent.run(
        {
            "plan": "crear un plugin para leer logs del sistema"
        }
    )

    print(salida)
