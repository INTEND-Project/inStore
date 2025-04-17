from .octo import OCTOLLM


def llm_factory(model_name: str = "octo"):
    if model_name == "octo":
        return OCTOLLM()
    return OCTOLLM()  # Default


from pkg.config import LLM, LLMInfo, OCTOConfig

from .octo import OCTOLLM


def llm_factory(llm_info: LLMInfo):
    if llm_info.provider == LLM.OCTO.value:
        cfg = OCTOConfig(llm_info.config)
        return OCTOLLM(llm_config=cfg)

    raise ValueError(f"Unknown LLM {llm_info.provider}")
