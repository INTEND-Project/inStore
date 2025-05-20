from pkg.config import LLM, LLMInfo, OCTOConfig
from pkg.config.llms import GeminiConfig

from .gemini import GeminiLLM
from .octo import OCTOLLM


def llm_factory(llm_info: LLMInfo):
    if llm_info.provider == LLM.OCTO.value:
        cfg = OCTOConfig(llm_info.config)
        return OCTOLLM(llm_config=cfg)
    if llm_info.provider == LLM.GEMINI.value:
        cfg = GeminiConfig(llm_info.config)
        return GeminiLLM(llm_config=cfg)

    raise ValueError(f"Unknown LLM {llm_info.provider}")
