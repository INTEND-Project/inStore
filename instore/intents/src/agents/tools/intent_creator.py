from typing import Optional

from langchain_core.callbacks import CallbackManagerForToolRun
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from pkg.interfaces import KnowledgeGraph


class IntentCreatorInput(BaseModel):
    intent_id: str = Field(description="Unique intent ID in UUID format.")
    commands: list[str] = Field(
        description="The list of commands that are going to be executed as a side effect of this intent."
    )


class IntentCreator(BaseTool):
    name: str = "IntentCreator"
    description: str = "Creates a new intent"

    knowledge_graph: KnowledgeGraph

    def _run(self, intent_id: str, commands: list[str], run_manager: Optional[CallbackManagerForToolRun] = None):
        return str(
            self.knowledge_graph.create_intent(
                user_name="John_Doe",
                intent_name=intent_id,
                commands=commands,
            )
        )
