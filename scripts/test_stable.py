"""Synthetic regression tests for native provider selection (no running server needed)."""
import contextlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import stable


class NativeImportTests(unittest.TestCase):
    def test_list_selects_exact_provider_instance(self):
        with patch.object(stable, "issue_token", return_value="test-token"), \
                patch.object(stable, "api", return_value={"sessions": []}) as api:
            stable.list_sessions("codex", "codex-personal")
        api.assert_called_once_with("test-token", "POST", "/api/agent-sessions/list",
                                    {"source": "codex", "providerInstanceId": "codex-personal"})

    def test_native_import_uses_selected_instance_in_payload_and_link(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / "userdata").mkdir()
            (base / "userdata/environment-id").write_text("test-environment")
            session = {"sessionId": "ses_example", "workspaceRoot": directory,
                       "title": "Synthetic session", "providerInstanceId": "opencode-personal"}
            calls = []

            def api(token, method, route, payload=None):
                calls.append((method, route, payload))
                if route == "/api/agent-sessions/list":
                    return {"sessions": [session]}
                if route == "/api/projects":
                    return {"projects": [{"id": "project", "deletedAt": None,
                                          "workspaceRoot": directory, "title": "Project"}]}
                if route.startswith("/api/orchestration/threads/"):
                    raise RuntimeError("GET failed (404)")
                if route == "/api/agent-sessions/import":
                    return {"importedCount": 1, "skippedCount": 0}
                self.fail(f"Unexpected API route: {route}")

            with patch.object(stable, "BASE", base), \
                    patch.object(stable, "issue_token", return_value="test-token"), \
                    patch.object(stable, "api", side_effect=api), \
                    contextlib.redirect_stdout(io.StringIO()):
                link = stable.import_session("ses_example", provider="opencode",
                                             instance="opencode-personal")
            self.assertTrue(link.endswith("/import%3Aopencode-personal%3Ases_example"))
            payload = next(payload for method, route, payload in calls
                           if route == "/api/agent-sessions/import")
            self.assertEqual(payload["source"], "opencode")
            self.assertEqual(payload["providerInstanceId"], "opencode-personal")
            self.assertEqual(payload["expectedWorkspaceRoot"], directory)

    def test_force_cannot_bypass_native_snapshot_checks(self):
        with patch.object(stable, "issue_token") as token:
            with self.assertRaisesRegex(RuntimeError, "cannot be bypassed"):
                stable.import_session("native-session", force=True, provider="codex")
            token.assert_not_called()

    def test_missing_native_session_does_not_create_a_project(self):
        with patch.object(stable, "issue_token", return_value="test-token"), \
                patch.object(stable, "api", return_value={"sessions": []}) as api:
            with self.assertRaisesRegex(RuntimeError, "selected provider instance"):
                stable.import_session("missing", provider="codex")
            self.assertEqual(api.call_count, 1)


if __name__ == "__main__":
    unittest.main()
