import os

from flask.testing import FlaskClient
from openapi_core import Config, OpenAPI
from openapi_core.contrib.werkzeug import WerkzeugOpenAPIRequest, WerkzeugOpenAPIResponse
from openapi_core.templating.paths.exceptions import OperationNotFound, PathNotFound

SPEC_PATH = os.path.join(os.path.dirname(__file__), "..", "openapi", "instore-v1.yaml")

openapi = OpenAPI.from_file_path(
    SPEC_PATH,
    # Server-Sent Event streams are documented as plain strings
    config=Config(extra_media_type_deserializers={"text/event-stream": lambda data: data.decode() if isinstance(data, bytes) else data}),
)


class SpecValidatingClient(FlaskClient):
    """Test client that checks every response against the OpenAPI spec."""

    def open(self, *args, **kwargs):
        response = super().open(*args, **kwargs)
        try:
            openapi.validate_response(WerkzeugOpenAPIRequest(response.request), WerkzeugOpenAPIResponse(response))
        except (PathNotFound, OperationNotFound):
            # Routes that are not part of the API, e.g. unknown routes and CORS preflight requests
            pass
        return response
