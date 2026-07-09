from agents.base_agent import BaseAgent
from planner_engine import crear_plan


class PlannerAgent(BaseAgent):

    def __init__(self):
        super().__init__("PlannerAgent")

    def run(self, objetivo):

        resultado = crear_plan(objetivo)

        self.remember(
            task=objetivo,
            result="PLAN_CREATED"
        )

        return {
            "agent": self.name,
            "decision": "PLAN_CREATED",
            "result": resultado
        }


if __name__ == "__main__":

    agent = PlannerAgent()

    salida = agent.run(
        "crear un plugin para leer logs del sistema"
    )

    print(salida)
