from enum import Enum
from typing import Any, Union


class LLM(Enum):
    OCTO = "octo"
    GEMINI = "gemini"
    MOCK = "mock"


class OCTOConfig:

    model_name: str
    model_name_pretty: str
    endpoint: str

    def __init__(self, cfg: dict[str, Any]):
        if cfg is not None:
            # If config is no longer flat, manually set each field
            for key, value in cfg.items():
                setattr(self, key, value)


class GeminiConfig:
    model_name: str
    model_name_pretty: str
    endpoint: str

    def __init__(self, cfg: dict[str, Any]):
        if cfg is not None:
            for key, value in cfg.items():
                setattr(self, key, value)


class MockConfig:

    model_name: str
    model_name_pretty: str

    def __init__(self, cfg):
        if cfg is not None:
            for key, value in cfg.items():
                setattr(self, key, value)


class LLMInfo:
    provider: str
    config: dict[str, Any]

    def __init__(self, cfg: dict[str, Any]):
        if cfg is not None:
            for key, value in cfg.items():
                setattr(self, key, value)
