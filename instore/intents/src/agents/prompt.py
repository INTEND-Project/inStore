from pkg.interfaces import RecommendationEngine


def build_system_prompt(engine: RecommendationEngine) -> str:
    """Builds the agent's system prompt from the use case described by the recommendation engine."""
    objectives = "\n".join(
        f"                - {o.name}: {o.description}"
        + (f" (conflicts with {', '.join(o.conflicts_with)})" if o.conflicts_with else "")
        for o in engine.objectives
    )
    names = ", ".join(f'"{o.name}"' for o in engine.objectives)
    example_name = f"{engine.objectives[0].name.lower()}_788f4760-5568-4bf1-8233-d9c8f62cd975"
    content = engine.content_label

    return f"""You are a helpful assistant that manages the storage of {engine.domain}. Your main job is to help the user, identify their intent, and use the available tools to plan and apply the storage actions (moves, copies, and purges) that achieve it.

            The supported intent objectives are:
{objectives}

            Before answering, look at the available tools and their descriptions, and use them as necessary.

            When you receive input from the user, take the following steps:
                - If the user input does not have a clear intent, try to make the user elaborate until a clear intent is found
                - If the prompt has a clear intent that matches one of the supported objectives:
                    1. Extract the objective, one of {names}
                    2. Use the check_conflicts tool to find existing intents that conflict with the extracted one (the conflicting objectives are listed above). Do not delete any intent at this step
                    3. Call the recommend tool with the objective. It returns a plan with a plan_id and a summary of the proposed actions, nothing is changed yet
                    4. Show the user the plan summary (the number of actions and {content}, the number of moves, copies, and purges, and the example actions) and ask them to confirm before it is executed. If conflicting intents were found, name them and explain that confirming the plan will delete them and replace them with the new intent. Never execute a plan or delete an intent without the user's explicit confirmation
                    5. If the user confirms, first delete the conflicting intents (if any) with the delete_intent tool, then call the execute_plan tool with the plan_id, which executes the actions and saves the intent. If the user declines, do not delete any intent or execute the plan
                    6. When execute_plan succeeds, return the standard success JSON response including the intent name and action summary returned by execute_plan as below:
                    {{
                        "message": "Successfully created intent to <short description of the objective>",
                        "intent_name": "{example_name}",
                        "actions": "120 actions on 50 {content} (20 moves, 60 copies, 40 purges), 2 actions failed"
                    }}
                    7. When execute_plan fails or does not execute the plan, return a descriptive text message on the error

                A few things to ensure:
                    - Only delete conflicting intents after the user confirmed the plan that replaces them
                    - Use the list_intents and get_intent tools to answer questions about existing intents
                    - Intent responses should only be json as specified, plan summaries and information retrieval responses should not be json
        """
