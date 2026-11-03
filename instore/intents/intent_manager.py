import argparse
import json
import os
from typing import Callable, Sequence

from dotenv import load_dotenv
from langchain_core.tools import BaseTool
from src.agents import Chatbot, Workflow, build_system_prompt, intent_tools, plan_tools
from src.api import create_app
from src.config import IntentManagerConfig
from src.plans import PlanStore
from src.service import IntentService

from pkg.db import knowledge_graph_factory
from pkg.engines import engine_factory
from pkg.executors import executor_factory
from pkg.llms import llm_factory


def main(cfg_path: str):
    print(f"Loading config: {cfg_path}")
    cfg = IntentManagerConfig(cfg=load_config(cfg_path))

    llm = llm_factory(llm_info=cfg.llm_info)

    kg = knowledge_graph_factory(info=cfg.kg_info)

    # In a dry run, the engine plans against mock data and the actions are logged instead of executed
    dry_run = os.environ.get("MOG_DRY_RUN", "").lower() in ("true", "1")
    engine = engine_factory(info=cfg.use_case.engine, dry_run=dry_run)
    executor = executor_factory(info=cfg.use_case.executor, dry_run=dry_run)
    print(f"Recommendation engine: {type(engine).__name__}, executor: {type(executor).__name__}")

    service = IntentService(
        engine=engine, executor=executor, knowledge_graph=kg, plan_store=PlanStore(), model_name=llm.get_model()
    )
    tools: Sequence[BaseTool] = [*intent_tools(service), *plan_tools(service)]

    chatbot = Chatbot(llm=llm, tools=tools, system_prompt=build_system_prompt(engine))

    def run_conversation(conversation_id: str, message: str, on_tool_call: Callable[[str], None]) -> str:
        workflow = Workflow(chatbot=chatbot, tools=tools, on_tool_callback=on_tool_call)
        result = workflow.run({"expression": message, "id": conversation_id})
        return result["messages"][-1].content

    # Optional, when set every route except the health check requires it in the X-API-Key header
    api_key = os.environ.get("INSTORE_API_KEY") or None
    print(f"API key required: {api_key is not None}")
    app = create_app(service=service, run_conversation=run_conversation, api_key=api_key)
    app.run(host="0.0.0.0", port=5001)


def load_config(file_path: str):
    with open(file_path, "r") as file:
        data = json.load(file)
        return data


if __name__ == "__main__":
    # Loaded before parsing arguments so INSTORE_CONFIG can be set in .env
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--cfg",
        help="config file path, defaults to the INSTORE_CONFIG env var or intents/config.json",
        type=str,
        default=os.environ.get("INSTORE_CONFIG") or "intents/config.json",
    )
    args = parser.parse_args()
    main(args.cfg)
