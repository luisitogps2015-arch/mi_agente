import json

class PlannerAgent:
    def run(self, objetivo):
        return {
            "agent": "PlannerAgent",
            "decision": "PLAN_CREATED"
        }


class ExecutorAgent:
    def run(self, objetivo):
        if "leer logs" in objetivo.lower():
            return {
                "agent": "ExecutorAgent",
                "decision": "PARCIAL"
            }

        return {
            "agent": "ExecutorAgent",
            "decision": "DESCONOCIDO"
        }


class CriticAgent:
    def run(self, objetivo):
        if "leer logs" in objetivo.lower():
            return {
                "agent": "CriticAgent",
                "decision": "CUMPLE_PARCIALMENTE"
            }

        return {
            "agent": "CriticAgent",
            "decision": "SIN_EVALUACION"
        }


class MultiAgentRouter:

    def __init__(self):
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.critic = CriticAgent()

    def run(self, objetivo):

        planner = self.planner.run(objetivo)
        executor = self.executor.run(objetivo)
        critic = self.critic.run(objetivo)

        return {
            "ok": True,
            "version": "MULTI_AGENT_V2_LOCAL",
            "objetivo": objetivo,
            "pipeline": {
                "planner": planner,
                "executor": executor,
                "critic": critic
            },
            "estado_final": critic["decision"]
        }


if __name__ == "__main__":

    objetivo = input("Objetivo: ")

    router = MultiAgentRouter()

    print(
        json.dumps(
            router.run(objetivo),
            indent=2,
            ensure_ascii=False
        )
    )
