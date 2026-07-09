import json

from agents.planner_agent import PlannerAgent
from agents.executor_agent import ExecutorAgent
from agents.critic_agent import CriticAgent
from agents.reflection_agent import ReflectionAgent
from agents.self_healing_agent import SelfHealingAgent
from agents.memory_agent import MemoryAgent


class MultiAgentRouter:

    def __init__(self):

        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.critic = CriticAgent()
        self.reflection = ReflectionAgent()
        self.healing = SelfHealingAgent()
        self.memory = MemoryAgent()

    def run(self, objetivo):

        resultado = {
            "ok": True,
            "version": "MULTI_AGENT_V2_REAL",
            "objetivo": objetivo,
            "pipeline": {}
        }

        planner = self.planner.run(objetivo)

        resultado["pipeline"]["planner"] = {
            "agent": planner["agent"],
            "decision": planner["decision"]
        }

        executor = self.executor.run(objetivo)

        resultado["pipeline"]["executor"] = {
            "agent": executor["agent"],
            "decision": executor["decision"]
        }

        critic = self.critic.run(objetivo)

        resultado["pipeline"]["critic"] = {
            "agent": critic["agent"],
            "decision": critic["decision"]
        }

        reflection = self.reflection.run(
            critic["result"]
        )

        resultado["pipeline"]["reflection"] = {
            "agent": reflection["agent"],
            "decision": reflection["decision"]
        }

        healing = self.healing.run(
            reflection["result"]
        )

        resultado["pipeline"]["self_healing"] = {
            "agent": healing["agent"],
            "decision": healing["decision"]
        }

        memory = self.memory.run()

        resultado["pipeline"]["memory"] = {
            "agent": memory["agent"],
            "decision": memory["decision"]
        }

        resultado["estado_final"] = healing["decision"]

        return resultado


if __name__ == "__main__":

    objetivo = input("Objetivo: ")

    router = MultiAgentRouter()

    salida = router.run(objetivo)

    print(
        json.dumps(
            salida,
            indent=2,
            ensure_ascii=False
        )
    )
