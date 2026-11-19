import hashlib
import io
import json
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

from integrations import HostelSamparkApiError, HostelSamparkClient


ROOT = Path(__file__).resolve().parents[1]


class TestPlatformIntegration(unittest.TestCase):
    def test_python_client_calls_config_without_a_key(self):
        response = io.BytesIO(b'{"hostels":["Saramati"]}')
        with patch("integrations.hostel_sampark_client.urlopen", return_value=response) as urlopen:
            result = HostelSamparkClient("https://sampark.example").get_config()

        self.assertEqual(result, {"hostels": ["Saramati"]})
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://sampark.example/api/v1/config")
        self.assertIsNone(request.get_header("Authorization"))

    def test_python_client_rejects_plain_http_remote_host(self):
        with self.assertRaisesRegex(ValueError, "must use HTTPS"):
            HostelSamparkClient("http://sampark.example", "private-api-key")

    def test_python_client_sends_key_only_for_private_api_calls(self):
        response = io.BytesIO(
            b'{"ticket_id":123,"lookup_code":"private-code"}'
        )
        with patch("integrations.hostel_sampark_client.urlopen", return_value=response) as urlopen:
            receipt = HostelSamparkClient(
                "https://sampark.example", "private-api-key"
            ).submit_grievance(
                "Broken light", "It is not working.", "Saramati", "Electrical", "ENROLL123"
            )

        self.assertEqual(receipt["ticket_id"], 123)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer private-api-key")
        self.assertEqual(json.loads(request.data), {
            "title": "Broken light",
            "description": "It is not working.",
            "hostel": "Saramati",
            "category": "Electrical",
            "enrollment_no": "ENROLL123",
        })

    def test_python_client_surfaces_api_errors_without_credentials(self):
        error = HTTPError(
            "https://sampark.example/api/v1/status",
            403,
            "Forbidden",
            {},
            io.BytesIO(b'{"error":"Key lacks permission."}'),
        )
        with patch("integrations.hostel_sampark_client.urlopen", side_effect=error):
            with self.assertRaises(HostelSamparkApiError) as raised:
                HostelSamparkClient(
                    "https://sampark.example", "private-api-key"
                ).get_status(123, "ENROLL123")

        self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(str(raised.exception), "Key lacks permission.")
        self.assertNotIn("private-api-key", str(raised.exception))

    def test_key_generator_outputs_hashed_scoped_client_config(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "integrations" / "generate_api_key.py"),
                "campus_portal",
                "grievance:submit",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
        lines = result.stdout.splitlines()
        token = lines[1]
        config_line = lines[4]
        config = json.loads(config_line)

        self.assertGreaterEqual(len(token), 40)
        self.assertEqual(
            config["campus_portal"]["key_hash"],
            hashlib.sha256(token.encode()).hexdigest(),
        )
        self.assertEqual(config["campus_portal"]["scopes"], ["grievance:submit"])


if __name__ == "__main__":
    unittest.main()
