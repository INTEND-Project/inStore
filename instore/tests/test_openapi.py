import re

import yaml
from openapi_spec_validator import validate

from fakes import InMemoryKnowledgeGraph
from openapi_validation import SPEC_PATH
from pkg.engines import MogCdnEngine
from pkg.executors import DryRunExecutor
from src.api import create_app
from src.plans import PlanStore
from src.service import IntentService


def load_spec():
    with open(SPEC_PATH) as f:
        return yaml.safe_load(f)


def test_spec_is_valid_openapi():
    validate(load_spec())


def test_spec_documents_exactly_the_implemented_routes():
    service = IntentService(MogCdnEngine(use_mock_videos=True), DryRunExecutor(), InMemoryKnowledgeGraph(), PlanStore())
    app = create_app(service=service, run_conversation=lambda *_: "")

    implemented = {
        (method.lower(), re.sub(r"<(?:\w+:)?(\w+)>", r"{\1}", rule.rule))
        for rule in app.url_map.iter_rules()
        if rule.endpoint != "static"
        for method in rule.methods - {"HEAD", "OPTIONS"}
    }
    documented = {
        (method, path)
        for path, item in load_spec()["paths"].items()
        for method in item
        if method in {"get", "post", "put", "patch", "delete"}
    }
    assert implemented == documented
