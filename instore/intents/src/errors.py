class ServiceError(Exception):
    """Error raised by the intent service, with the HTTP status and code the REST API reports it with."""

    http_status = 400
    code = "invalid_request"

    def __init__(self, message: str, details=None):
        super().__init__(message)
        self.message = message
        self.details = details


class InvalidRequest(ServiceError):
    http_status = 400
    code = "invalid_request"


class NotFound(ServiceError):
    http_status = 404
    code = "not_found"


class ConflictingIntents(ServiceError):
    http_status = 409
    code = "conflicting_intents"


class PlanAlreadyExecuted(ServiceError):
    http_status = 409
    code = "plan_already_executed"


class PlanExpired(ServiceError):
    http_status = 410
    code = "plan_expired"


class ExecutionFailed(ServiceError):
    http_status = 502
    code = "execution_failed"
