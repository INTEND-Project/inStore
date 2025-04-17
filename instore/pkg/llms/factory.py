from .octo import OCTOLLM


def llm_factory(model_name: str = "octo"):
    if model_name == "octo":
        return OCTOLLM()
    return OCTOLLM()  # Default
