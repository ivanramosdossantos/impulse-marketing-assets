import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "upload_from_file.py"
spec = importlib.util.spec_from_file_location("marketing_upload", SCRIPT)
uploader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uploader)
VALID_PNG = b"\x89PNG\r\n\x1a\n" + b"test fixture binary content"


class UploadTests(unittest.TestCase):
    def test_rejects_traversal_and_unapproved_paths(self):
        for p in ("../secrets.png", "posts/../secrets.png", "docs/x.jpg", "posts/x.txt", "posts/x file.png"):
            with self.subTest(p=p), self.assertRaises(ValueError):
                uploader.validate_target(p)

    def test_file_type_and_length_validation(self):
        uploader.validate_media(VALID_PNG, ".png")
        with self.assertRaises(ValueError):
            uploader.validate_media(b"not a PNG", ".png")
        with self.assertRaises(ValueError):
            uploader.validate_media(b"", ".png")

    def test_base64_git_request_and_sha(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "file.png"
            source.write_bytes(VALID_PNG)
            calls = []

            def fake_api(token, path, method, body=None):
                calls.append((token, path, method, body))
                if method == "GET":
                    return 404, None
                return 201, {
                    "commit": {"sha": "abc123"},
                    "content": {"html_url": "https://github.com/example/file"},
                }

            with patch.object(uploader, "api_call", side_effect=fake_api):
                result = uploader.upload(source, "posts/2026/11/new.png", "test-token")
            payload = json.loads(calls[1][3])
            self.assertEqual(base64.b64decode(payload["content"]), VALID_PNG)
            self.assertEqual(result["size_bytes"], len(VALID_PNG))
            self.assertEqual(result["sha256"], hashlib.sha256(VALID_PNG).hexdigest())
            self.assertEqual(result["commit_sha"], "abc123")

    def test_never_overwrites_existing_file(self):
        with tempfile.TemporaryDirectory() as d:
            source = Path(d) / "file.png"
            source.write_bytes(VALID_PNG)
            with patch.object(uploader, "api_call", return_value=(200, {})) as api:
                with self.assertRaises(FileExistsError):
                    uploader.upload(source, "posts/2026/11/exists.png", "token")
            self.assertEqual(api.call_count, 1)


if __name__ == "__main__":
    unittest.main()
