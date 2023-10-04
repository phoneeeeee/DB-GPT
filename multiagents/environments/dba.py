import asyncio
import logging
from typing import Any, Dict, List, Tuple, Union
from enum import Enum
from colorama import Fore
import json

from multiagents.utils.utils import AGENT_TYPES
from multiagents.agents.conversation_agent import BaseAgent
from multiagents.message import Message, SolverMessage

from multiagents.environments.decision_maker import (
    BaseDecisionMaker,
    DynamicDecisionMaker,
    decision_maker_registry,
)
from multiagents.environments.role_assigner import (
    BaseRoleAssigner,
    role_assigner_registry,
)

from . import env_registry as EnvironmentRegistry
# from .base import BaseEnvironment
from pydantic import BaseModel


@EnvironmentRegistry.register("dba")
class DBAEnvironment(BaseModel):
    """
    A basic environment implementing the logic of conversation.

    Args:
        agents: List of agents
        rule: Rule for the environment
        max_loop_rounds: Maximum number of loop rounds number
        cnt_turn: Current round number
        last_messages: Messages from last turn
        rule_params: Variables set by the rule
    """

    agents: Dict[Enum, Union[BaseAgent, List[BaseAgent]]] = None
    role_assigner: BaseRoleAssigner
    decision_maker: BaseDecisionMaker
    # executor: BaseExecutor
    # evaluator: BaseEvaluator

    task_description: str

    cnt_turn: int = 0
    max_turn: int = 10
    success: bool = False
    
    def __init__(self, **kwargs):
        def build_components(config: Dict, registry):
            component_type = config.pop("type")
            component = registry.build(component_type, **config)
            return component

        role_assigner = build_components(
            kwargs.pop("role_assigner", {"type": "role_description"}),
            role_assigner_registry,
        )

        decision_maker = build_components(
            kwargs.pop("decision_maker", {"type": "vertical"}),
            decision_maker_registry,
        )
        # executor = build_components(
        #     kwargs.pop("executor", {"type": "none"}), executor_registry
        # )
        # evaluator = build_components(
        #     kwargs.pop("evaluator", {"type": "basic"}), evaluator_registry
        # )

        super().__init__(
            role_assigner=role_assigner,
            decision_maker=decision_maker,
            # executor=executor,
            # evaluator=evaluator,
            **kwargs,
        )

    async def step(
        self, advice: str = "No advice yet.", previous_plan: str = "No solution yet."
    ) -> List[Message]:
        
        # advice = "No advice yet."
        result = ""
        # previous_plan = "No solution yet."
        logs = []

        # ================== EXPERT RECRUITMENT ==================
        agents = self.role_assign(advice=advice, alert_info=self.role_assigner.alert_str)

        # assign alert info to each agent
        for agent in agents:
            agent.alert_str = self.role_assigner.alert_str
            agent.alert_dict = self.role_assigner.alert_dict
        
        # ================== EXPERT DIAGNOSIS ==================
        # count on these experts to diagnose for the alert        
        plans = await self.decision_making(agents, None, previous_plan, advice) # plans: the list of diagnosis messages

        # ================== Report Generation ==================
        # discuss over the diagnosis results
        # messages = await self.agents[i].astep(env_descriptions[i]) for i in agent_ids]
            

        # # Get the next agent index
        # agent_ids = self.rule.get_next_agent_idx(self)

        # # Generate current environment description
        # env_descriptions = self.rule.get_env_description(self)

        # # Generate the next message
        # messages = await asyncio.gather(
        #     *[self.agents[i].astep(env_descriptions[i]) for i in agent_ids]
        # )

        # # Some rules will select certain messages from all the messages
        # selected_messages = self.rule.select_message(self, messages)
        # # pdb.set_trace()        
        # self.last_messages = selected_messages
        
        # self.print_messages(selected_messages)

        # # Update the memory of the agents
        # self.rule.update_memory(self)

        # # Update the set of visible agents for each agent
        # self.rule.update_visible_agents(self)


        # Although plan may be a list in some cases, all the cases we currently consider
        # only have one plan, so we just take the first element.
        # TODO: make it more general
        # plan = plan[0].content

        import pdb; pdb.set_trace()
        
        return result, advice, logs, self.success

    def role_assign(self, advice: str = "", alert_info: str = "") -> List[BaseAgent]:
        """Assign roles to agents"""

        agents = self.role_assigner.step(
            role_assigner=self.agents[AGENT_TYPES.ROLE_ASSIGNMENT][0],
            group_members=self.agents[AGENT_TYPES.SOLVER],
            advice=advice,
            alert_info=alert_info
        )
        
        return agents

    async def decision_making(
        self,
        agents: List[BaseAgent],
        manager: List[BaseAgent],
        previous_plan: str,
        advice: str = "No advice yet.",
    ) -> List[SolverMessage]:
        # TODO: plan should be string or a special type of object?

        # dynamic
        plans = await self.decision_maker.astep(
            agents=agents,
            task_description=self.task_description,
            previous_plan=previous_plan,
            advice=advice,
        )
        return plans

    def is_done(self):
        """Check if the environment is done"""
        return self.cnt_turn >= self.max_turn or self.success

    def set_task_description(self, task_description: str = ""):
        self.task_description = task_description

    def reset(self) -> None:
        """Reset the environment"""
        self.cnt_turn = 0
        # self.rule.reset()
        # self.role_assigner.reset()
        # self.solver.reset()
        # for critic in self.critics:
        #     critic.reset()
        # self.evaluator.reset()