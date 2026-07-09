from agents.base_agent import BaseAgent
from memory_manager import leer_resumen


class MemoryAgent(BaseAgent):

    def __init__(self):
        super().__init__("MemoryAgent")

    def run(self):

        resultado = leer_resumen()

        self.remember(
            task="memory_summary",
            result="MEMORY_READ"
        )

        return {
            "agent": self.name,
            "decision": "MEMORY_READ",
            "result": resultado
        }


if __name__ == "__main__":

    agent = MemoryAgent()

    salida = agent.run()

    print(salida)
