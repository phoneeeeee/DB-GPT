from __future__ import annotations
import asyncio
from colorama import Fore

from typing import TYPE_CHECKING, List

from . import decision_maker_registry
from .base import BaseDecisionMaker

if TYPE_CHECKING:
    from multiagents.agents import BaseAgent, SolverAgent, CriticAgent
    from multiagents.message import Message, CriticMessage, SolverMessage


@decision_maker_registry.register("vertical")
class VerticalDecisionMaker(BaseDecisionMaker):
    """
    Discuss in a vertical manner.
    """

    name: str = "vertical"

    async def astep(
        self,
        agents: List[BaseAgent],
        task_description: str,
        previous_plan: str = "No solution yet.",
        advice: str = "No advice yet.",
        *args,
        **kwargs,
    ) -> List[dict]:

        if len(agents) > 1:
            agents = agents[:2]

        results = await asyncio.gather(
            *[
                agent.step(previous_plan, advice, task_description)
                for agent in agents
            ]
        )

        # review by chief dba

        import pdb; pdb.set_trace()

        nonempty_results = []
        for result in results:
            if result["content"] != "":
                nonempty_results.append(result)

        agents[0].add_message_to_memory(nonempty_results) # agents[9].memory

        return nonempty_results

    def reset(self):
        pass
