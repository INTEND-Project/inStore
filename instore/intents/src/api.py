import json
import queue
import threading
from typing import Any, Callable, Iterator, Optional

from flask import Blueprint, Flask, Response, jsonify, request
from flask_cors import CORS
from pydantic import BaseModel, Field, ValidationError
from werkzeug.exceptions import HTTPException

from .errors import InvalidRequest, ServiceError
from .plans import Plan
from .service import IntentService

API_PREFIX = "/api/v1"

# Runs one conversation turn: (conversation_id, message, on_tool_call) -> reply
RunConversation = Callable[[str, str, Callable[[str], None]], str]


class RecommendationRequest(BaseModel):
    objective: str = Field(min_length=1)
    params: Optional[dict[str, Any]] = None


class MessageRequest(BaseModel):
    message: str = Field(min_length=1)


def stream_conversation(run_conversation: RunConversation, conversation_id: str, message: str) -> Iterator[str]:
    """Runs a conversation turn in a thread and streams its progress and reply as Server-Sent Events."""
    events: queue.Queue = queue.Queue()

    def run():
        try:
            reply = run_conversation(conversation_id, message, lambda m: events.put({"type": "tool_call", "message": m}))
            events.put({"type": "response", "reply": reply})
        except Exception as e:
            events.put({"type": "error", "message": str(e)})
        finally:
            events.put(None)

    threading.Thread(target=run, daemon=True).start()
    while (event := events.get()) is not None:
        yield f"data: {json.dumps(event)}\n\n"


def create_app(service: IntentService, run_conversation: RunConversation) -> Flask:
    app = Flask(__name__)
    CORS(app)
    app.register_blueprint(_api_v1(service, run_conversation), url_prefix=API_PREFIX)
    _register_error_handlers(app)
    _register_legacy_routes(app, service, run_conversation)
    return app


def _api_v1(service: IntentService, run_conversation: RunConversation) -> Blueprint:
    api = Blueprint("api_v1", __name__)

    @api.get("/health")
    def health():
        kg_ok = service.knowledge_graph.is_healthy()
        body = {
            "status": "ok" if kg_ok else "unavailable",
            "knowledge_graph": "ok" if kg_ok else "unreachable",
            "dry_run": service.executor.dry_run,
        }
        return jsonify(body), 200 if kg_ok else 503

    @api.get("/capabilities")
    def capabilities():
        return jsonify(service.capabilities())

    @api.get("/intents")
    def list_intents():
        intents = service.list_intents(objective=request.args.get("objective"))
        return jsonify([_intent(i) for i in intents])

    @api.get("/intents/<name>")
    def get_intent(name: str):
        return jsonify(_intent(service.get_intent(name)))

    @api.get("/intents/<name>/actions")
    def get_intent_actions(name: str):
        return jsonify([_stored_action(c) for c in service.get_intent(name)["commands"]])

    @api.delete("/intents/<name>")
    def delete_intent(name: str):
        service.delete_intent(name)
        return "", 204

    @api.post("/recommendations")
    def recommend():
        body = _parse(RecommendationRequest)
        plan = service.recommend(objective=body.objective, params=body.params)
        return jsonify(_plan(plan)), 201

    @api.post("/recommendations/<plan_id>/execute")
    def execute_plan(plan_id: str):
        result = service.execute_plan(plan_id)
        body = {
            "intent_name": result.intent_name,
            "summary": result.summary,
            "actions": [
                {**_action(r.action), "status": "succeeded" if r.ok else "failed", "error": r.error}
                for r in result.results
            ],
        }
        return jsonify(body), 201

    @api.post("/conversations/<conversation_id>/messages")
    def send_message(conversation_id: str):
        body = _parse(MessageRequest)
        return Response(stream_conversation(run_conversation, conversation_id, body.message), mimetype="text/event-stream")

    return api


def _register_error_handlers(app: Flask):
    def error(status: int, code: str, message: str, details=None):
        return jsonify({"error": {"code": code, "message": message, "details": details}}), status

    @app.errorhandler(ServiceError)
    def service_error(e: ServiceError):
        return error(e.http_status, e.code, e.message, e.details)

    @app.errorhandler(HTTPException)
    def http_error(e: HTTPException):
        if not request.path.startswith(API_PREFIX):
            return e
        return error(e.code or 500, (e.name or "error").lower().replace(" ", "_"), e.description or "")

    @app.errorhandler(Exception)
    def unexpected_error(e: Exception):
        if isinstance(e, HTTPException):
            return http_error(e)
        app.logger.exception(e)
        return error(500, "internal_error", str(e))


def _register_legacy_routes(app: Flask, service: IntentService, run_conversation: RunConversation):
    """Routes used by the UI before /api/v1, kept for compatibility. Deprecated."""

    @app.post("/intent")
    def legacy_send_message():
        body = request.get_json(silent=True) or {}
        return Response(
            stream_conversation(run_conversation, body.get("id", ""), body.get("expression", "")),
            mimetype="text/event-stream",
        )

    @app.get("/intent")
    def legacy_list_intents():
        return Response(status=200, response=json.dumps(service.list_intents()), mimetype="application/json")

    @app.get("/intent/<name>")
    def legacy_get_intent(name: str):
        intent = service.knowledge_graph.get_intent(name)
        if intent is None:
            return Response(status=404, response=json.dumps({"error": f"Intent {name} not found"}), mimetype="application/json")
        return Response(status=200, response=json.dumps(intent), mimetype="application/json")

    # Doesn't work properly, not part of /api/v1
    @app.get("/device/<name>")
    def legacy_get_device(name: str):
        return Response(status=200, response=json.dumps(service.knowledge_graph.get_device(name)))


def _parse(model: type[BaseModel]) -> Any:
    body = request.get_json(silent=True)
    if body is None:
        raise InvalidRequest("The request body must be a JSON object")
    try:
        return model.model_validate(body)
    except ValidationError as e:
        raise InvalidRequest("Invalid request body", details=e.errors(include_url=False, include_context=False))


def _intent(i: dict[str, Any]) -> dict[str, Any]:
    commands = i.get("commands", [])
    return {
        "name": i["name"],
        "objective": i["objective"],
        "active_from": i.get("from"),
        # None means the intent has no end
        "active_until": None if i.get("to") in (None, "never") else i.get("to"),
        "action_count": len(commands),
        "failed_action_count": sum(1 for c in commands if c.get("status") == "failed"),
    }


def _action(a) -> dict[str, Any]:
    return {"type": a.type, "content_id": a.content_id, "source": a.source, "destination": a.destination}


def _stored_action(c: dict[str, Any]) -> dict[str, Any]:
    return {
        "type": c.get("cmd"),
        "content_id": c.get("content_id"),
        "source": c.get("source"),
        "destination": c.get("destination"),
        "executed_at": c.get("date_time"),
        "status": c.get("status"),
        "error": c.get("error"),
    }


def _plan(plan: Plan) -> dict[str, Any]:
    by_type: dict[str, int] = {}
    for a in plan.actions:
        by_type[a.type] = by_type.get(a.type, 0) + 1
    return {
        "plan_id": plan.id,
        "objective": plan.objective,
        "created_at": plan.created_at.isoformat(timespec="seconds"),
        "expires_at": plan.expires_at.isoformat(timespec="seconds") if plan.expires_at else None,
        "summary": {
            "action_count": len(plan.actions),
            "content_count": len({a.content_id for a in plan.actions}),
            "by_type": by_type,
        },
        "actions": [_action(a) for a in plan.actions],
    }
