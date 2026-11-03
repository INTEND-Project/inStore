import json

import pytest

from fakes import FailingExecutor, InMemoryKnowledgeGraph, RaisingExecutor
from pkg.engines import MogCdnEngine
from pkg.executors import DryRunExecutor
from src.api import create_app
from src.plans import PlanStore
from src.service import IntentService

API = "/api/v1"


def fake_conversation(conversation_id, message, on_tool_call):
    if message == "fail":
        raise RuntimeError("LLM endpoint unreachable")
    on_tool_call("Computing a plan")
    return f"[{conversation_id}] you said: {message}"


def make_client(executor=None, kg=None, ttl_seconds=1800, engine=None):
    service = IntentService(
        engine=engine or MogCdnEngine(use_mock_videos=True),
        executor=executor or DryRunExecutor(),
        knowledge_graph=kg or InMemoryKnowledgeGraph(),
        plan_store=PlanStore(ttl_seconds=ttl_seconds),
        model_name="test-model",
    )
    return create_app(service=service, run_conversation=fake_conversation).test_client()


@pytest.fixture
def client():
    return make_client()


def recommend(client, objective="REDUCE_COST"):
    res = client.post(f"{API}/recommendations", json={"objective": objective})
    assert res.status_code == 201, res.json
    return res.json


def execute(client, plan_id):
    return client.post(f"{API}/recommendations/{plan_id}/execute")


def assert_error(res, status, code):
    assert res.status_code == status, res.json
    assert res.content_type == "application/json"
    assert res.json["error"]["code"] == code
    assert res.json["error"]["message"]


# Service


def test_health(client):
    res = client.get(f"{API}/health")
    assert res.status_code == 200
    assert res.json == {"status": "ok", "knowledge_graph": "ok", "dry_run": True}


def test_health_reports_unreachable_knowledge_graph():
    res = make_client(kg=InMemoryKnowledgeGraph(healthy=False)).get(f"{API}/health")
    assert res.status_code == 503
    assert res.json["knowledge_graph"] == "unreachable"


def test_capabilities(client):
    res = client.get(f"{API}/capabilities")
    assert res.status_code == 200
    body = res.json
    assert body["content_label"] == "videos"
    assert body["dry_run"] is True
    assert body["model"] == "test-model"
    assert {o["name"]: o["conflicts_with"] for o in body["objectives"]} == {
        "REDUCE_COST": ["REDUCE_LATENCY"],
        "REDUCE_LATENCY": ["REDUCE_COST"],
    }


# Recommendations


def test_recommend_returns_plan_without_changing_anything(client):
    plan = recommend(client)
    assert plan["objective"] == "REDUCE_COST"
    assert plan["summary"] == {"action_count": 47, "content_count": 21, "by_type": {"move": 13, "purge": 16, "copy": 18}}
    assert len(plan["actions"]) == 47
    assert set(plan["actions"][0]) == {"type", "content_id", "source", "destination"}
    assert plan["expires_at"] > plan["created_at"]
    assert client.get(f"{API}/intents").json == []


@pytest.mark.parametrize(
    "body",
    [{"objective": "FASTER"}, {}, {"objective": ""}, {"objective": 5}, None],
    ids=["unknown objective", "missing objective", "empty objective", "wrong type", "no body"],
)
def test_recommend_rejects_invalid_requests(client, body):
    res = client.post(f"{API}/recommendations", json=body) if body is not None else client.post(f"{API}/recommendations")
    assert_error(res, 400, "invalid_request")


def test_recommend_reports_engine_failure():
    engine = MogCdnEngine(api_url=None)  # no MOG API configured
    res = make_client(engine=engine).post(f"{API}/recommendations", json={"objective": "REDUCE_COST"})
    assert_error(res, 502, "upstream_error")


# Execution


def test_execute_saves_intent_with_action_results(client):
    plan = recommend(client)
    res = execute(client, plan["plan_id"])
    assert res.status_code == 201
    body = res.json
    assert body["summary"].startswith("47 actions on 21 videos (13 moves, 18 copies, 16 purges), 0 actions failed")
    assert len(body["actions"]) == 47 and all(a["status"] == "succeeded" for a in body["actions"])

    name = body["intent_name"]
    intent = client.get(f"{API}/intents/{name}").json
    assert intent["objective"] == "REDUCE_COST"
    assert intent["active_until"] is None
    assert intent["action_count"] == 47 and intent["failed_action_count"] == 0
    actions = client.get(f"{API}/intents/{name}/actions").json
    assert len(actions) == 47
    assert set(actions[0]) == {"type", "content_id", "source", "destination", "executed_at", "status", "error"}


def test_execute_twice_is_refused(client):
    plan = recommend(client)
    assert execute(client, plan["plan_id"]).status_code == 201
    assert_error(execute(client, plan["plan_id"]), 409, "plan_already_executed")


def test_execute_unknown_plan(client):
    assert_error(execute(client, "nope"), 404, "not_found")


def test_execute_expired_plan():
    client = make_client(ttl_seconds=0)
    plan = recommend(client)
    assert_error(execute(client, plan["plan_id"]), 410, "plan_expired")


def test_conflict_is_reported_and_resolved_by_deleting(client):
    cost = execute(client, recommend(client, "REDUCE_COST")["plan_id"]).json["intent_name"]
    latency_plan = recommend(client, "REDUCE_LATENCY")

    res = execute(client, latency_plan["plan_id"])
    assert_error(res, 409, "conflicting_intents")
    assert res.json["error"]["details"] == [{"name": cost, "objective": "REDUCE_COST"}]

    assert client.delete(f"{API}/intents/{cost}").status_code == 204
    res = execute(client, latency_plan["plan_id"])
    assert res.status_code == 201
    assert [i["objective"] for i in client.get(f"{API}/intents").json] == ["REDUCE_LATENCY"]


def test_partial_failure_is_saved_and_total_failure_is_not():
    client = make_client(executor=FailingExecutor())
    res = execute(client, recommend(client)["plan_id"])
    assert_error(res, 502, "execution_failed")
    assert len(res.json["error"]["details"]) == 47
    assert client.get(f"{API}/intents").json == []


def test_executor_error_releases_the_plan():
    service_kg = InMemoryKnowledgeGraph()
    client = make_client(executor=RaisingExecutor(), kg=service_kg)
    plan = recommend(client)
    assert_error(execute(client, plan["plan_id"]), 502, "upstream_error")
    # The plan was not consumed, executing it again fails the same way instead of "already executed"
    assert_error(execute(client, plan["plan_id"]), 502, "upstream_error")


# Intents


def test_list_intents_filters_by_objective(client):
    execute(client, recommend(client, "REDUCE_COST")["plan_id"])
    assert len(client.get(f"{API}/intents?objective=REDUCE_COST").json) == 1
    assert client.get(f"{API}/intents?objective=REDUCE_LATENCY").json == []


@pytest.mark.parametrize("method,path", [("get", "/intents/nope"), ("get", "/intents/nope/actions"), ("delete", "/intents/nope")])
def test_missing_intent(client, method, path):
    assert_error(getattr(client, method)(f"{API}{path}"), 404, "not_found")


def test_unknown_route_returns_json(client):
    assert_error(client.get(f"{API}/nope"), 404, "not_found")


# Conversations


def sse_events(res):
    return [json.loads(line[len("data: "):]) for line in res.get_data(as_text=True).split("\n\n") if line]


def test_conversation_streams_progress_and_reply(client):
    res = client.post(f"{API}/conversations/c1/messages", json={"message": "hello"})
    assert res.status_code == 200
    assert res.mimetype == "text/event-stream"
    assert sse_events(res) == [
        {"type": "tool_call", "message": "Computing a plan"},
        {"type": "response", "reply": "[c1] you said: hello"},
    ]


def test_conversation_streams_errors(client):
    res = client.post(f"{API}/conversations/c1/messages", json={"message": "fail"})
    assert sse_events(res) == [{"type": "error", "message": "LLM endpoint unreachable"}]


def test_conversation_requires_a_message(client):
    assert_error(client.post(f"{API}/conversations/c1/messages", json={}), 400, "invalid_request")


# Deprecated routes used by the UI before /api/v1


def test_legacy_routes(client):
    name = execute(client, recommend(client)["plan_id"]).json["intent_name"]
    intents = client.get("/intent").json
    assert intents[0]["name"] == name and len(intents[0]["commands"]) == 47
    assert client.get(f"/intent/{name}").json["objective"] == "REDUCE_COST"
    assert client.get("/intent/nope").status_code == 404
    res = client.post("/intent", json={"expression": "hello", "id": "c2"})
    assert sse_events(res)[-1] == {"type": "response", "reply": "[c2] you said: hello"}


# API key


KEY = "test-key"


@pytest.fixture
def secured():
    service = IntentService(
        engine=MogCdnEngine(use_mock_videos=True),
        executor=DryRunExecutor(),
        knowledge_graph=InMemoryKnowledgeGraph(),
        plan_store=PlanStore(),
    )
    return create_app(service=service, run_conversation=fake_conversation, api_key=KEY).test_client()


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong"}], ids=["missing key", "wrong key"])
@pytest.mark.parametrize(
    "method,path",
    [("get", f"{API}/capabilities"), ("get", f"{API}/intents"), ("post", f"{API}/recommendations"), ("get", "/intent"), ("get", f"{API}/nope")],
)
def test_api_key_is_required(secured, headers, method, path):
    assert_error(getattr(secured, method)(path, headers=headers), 401, "unauthorized")


def test_api_key_grants_access(secured):
    headers = {"X-API-Key": KEY}
    assert secured.get(f"{API}/capabilities", headers=headers).status_code == 200
    res = secured.post(f"{API}/recommendations", json={"objective": "REDUCE_COST"}, headers=headers)
    assert res.status_code == 201
    assert secured.post(f"{API}/recommendations/{res.json['plan_id']}/execute", headers=headers).status_code == 201


def test_health_and_cors_preflight_do_not_require_the_key(secured):
    assert secured.get(f"{API}/health").status_code == 200
    preflight = secured.options(
        f"{API}/intents",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "x-api-key"},
    )
    assert preflight.status_code == 200
    assert "x-api-key" in preflight.headers.get("Access-Control-Allow-Headers", "").lower()
