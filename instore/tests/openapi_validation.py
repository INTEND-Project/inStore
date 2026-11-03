import os

from flask.testing import FlaskClient
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request
from openapi_core import Config, OpenAPI
from openapi_core.contrib.werkzeug import WerkzeugOpenAPIRequest, WerkzeugOpenAPIResponse
from openapi_core.templating.paths.exceptions import OperationNotFound, PathNotFound

SPEC_PATH = os.path.join(os.path.dirname(__file__), "..", "openapi", "instore-v1.yaml")


def _as_text(data):
    return data.decode() if isinstance(data, bytes) else data


openapi = OpenAPI.from_file_path(
    SPEC_PATH,
    # Server-Sent Event streams, the spec, and the docs page are documented as plain strings
    config=Config(extra_media_type_deserializers={t: _as_text for t in ("text/event-stream", "application/yaml", "text/html")}),
)


class SpecValidatingClient(FlaskClient):
    """Test client that checks every response against the OpenAPI spec."""

    def open(self, *args, **kwargs):
        response = super().open(*args, **kwargs)
        # Response validation needs the method, path, and headers of the request, but not its body, which the app
        # already read. On Python 3.10, openapi-core reads the body again when checking the request type.
        sent = response.request
        request = Request(
            EnvironBuilder(
                method=sent.method,
                path=sent.path,
                query_string=sent.query_string.decode(),
                headers=list(sent.headers),
                base_url=sent.host_url,
            ).get_environ()
        )
        try:
            openapi.validate_response(WerkzeugOpenAPIRequest(request), WerkzeugOpenAPIResponse(response))
        except (PathNotFound, OperationNotFound):
            # Routes that are not part of the API, e.g. unknown routes and CORS preflight requests
            pass
        return response
