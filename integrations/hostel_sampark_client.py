import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class HostelSamparkApiError(RuntimeError):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code


class HostelSamparkClient:
    """Small server-side Python client for the Hostel Sampark JSON API."""

    def __init__(self, base_url, api_key=None, timeout=15):
        base_url = base_url.strip()
        parts = urlsplit(base_url)
        try:
            parts.port
        except ValueError as error:
            raise ValueError("base_url has an invalid port.") from error
        if (
            parts.scheme not in {"https", "http"}
            or not parts.netloc
            or parts.username is not None
            or parts.password is not None
            or parts.query
            or parts.fragment
            or (
                parts.scheme != "https"
                and parts.hostname not in {"localhost", "127.0.0.1", "::1"}
            )
        ):
            raise ValueError(
                "base_url must use HTTPS (HTTP is allowed only for local testing)."
            )
        self.base_url = base_url.rstrip("/")
        self._api_key = api_key.strip() if api_key else None
        self.timeout = timeout

    def get_config(self):
        return self._request("GET", "/api/v1/config")

    def submit_grievance(self, title, description, hostel, category, enrollment_no):
        return self._request(
            "POST",
            "/api/v1/submit",
            {
                "title": title,
                "description": description,
                "hostel": hostel,
                "category": category,
                "enrollment_no": enrollment_no,
            },
            authenticated=True,
        )

    def get_status(self, ticket_id, enrollment_no=None):
        payload = {"ticket_id": ticket_id}
        if enrollment_no:
            payload["enrollment_no"] = enrollment_no
        return self._request(
            "POST",
            "/api/v1/status",
            payload,
            authenticated=True,
        )

    def _request(self, method, path, body=None, authenticated=False):
        headers = {"Accept": "application/json"}
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if authenticated:
            if self._api_key is None:
                raise ValueError("This API action needs a platform API key.")
            headers["Authorization"] = f"Bearer {self._api_key}"

        request = Request(
            f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = response.read()
        except HTTPError as error:
            try:
                message = json.loads(error.read().decode("utf-8")).get(
                    "error", "The API request failed."
                )
            except (UnicodeDecodeError, json.JSONDecodeError, AttributeError):
                message = "The API request failed."
            raise HostelSamparkApiError(error.code, message) from None
        except URLError as error:
            raise HostelSamparkApiError(
                0, "Could not connect to the Hostel Sampark API."
            ) from error

        try:
            result = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise HostelSamparkApiError(
                0, "The API returned an invalid response."
            ) from error
        if not isinstance(result, dict):
            raise HostelSamparkApiError(0, "The API returned an invalid response.")
        return result
