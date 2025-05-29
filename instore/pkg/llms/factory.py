from pkg.config import LLM, LLMInfo, VLLMConfig
from pkg.config.llms import GeminiConfig

from .gemini import GeminiLLM
from .vllm import VLLM


def llm_factory(llm_info: LLMInfo):
    if llm_info.provider == LLM.VLLM.value:
        cfg = VLLMConfig(llm_info.config)
        return VLLM(llm_config=cfg)
    if llm_info.provider == LLM.GEMINI.value:
        cfg = GeminiConfig(llm_info.config)
        return GeminiLLM(llm_config=cfg)

    raise ValueError(f"Unknown LLM {llm_info.provider}")
