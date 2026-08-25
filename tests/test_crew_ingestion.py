import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import requests

import app as app_module
from crew_core.ingestion import (
    IngestionError,
    IngestionRegistry,
    IngestionTimeoutError,
    MAX_RESPONSE_BYTES,
    fetch_api_source,
)
from crew_core.run_service import (
    CrewRunBusyError,
    CrewRunRateLimitError,
    CrewRunRateLimiter,
    CrewRunRegistry,
    validate_input_data,
)
from crew_core.runner import run_research_crew


TOKEN = "test-dashboard-token"
AUTH_HEADERS = {"Authorization": f"Bearer {TOKEN}"}


class FakeResponse:
    def __init__(self, body=b"{}", status=200, content_type="application/json"):
        self.body = body
        self.status_code = status
        self.headers = {"Content-Type": content_type}
        self.encoding = "utf-8"
        self.closed = False

    def iter_content(self, chunk_size=8192):
        del chunk_size
        yield self.body

    def close(self):
        self.closed = True


class IngestionHttpTests(unittest.TestCase):
    @patch("crew_core.ingestion.requests.get")
    def test_allowed_source_returns_normalized_json_and_disables_redirects(self, get):
        get.return_value = FakeResponse(
            json.dumps({"id": 1, "title": "dato real"}).encode()
        )
        result = fetch_api_source("jsonplaceholder_todo")
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["data"]["title"], "dato real")
        self.assertIn("dato real", result["preview"])
        self.assertFalse(get.call_args.kwargs["allow_redirects"])

    @patch("crew_core.ingestion.requests.get", side_effect=requests.Timeout)
    def test_timeout_is_safe(self, get):
        del get
        with self.assertRaisesRegex(IngestionTimeoutError, "tiempo de espera"):
            fetch_api_source()

    @patch("crew_core.ingestion.requests.get")
    def test_http_error(self, get):
        get.return_value = FakeResponse(status=503)
        with self.assertRaisesRegex(IngestionError, "error HTTP"):
            fetch_api_source()

    @patch("crew_core.ingestion.requests.get")
    def test_redirect_is_rejected(self, get):
        get.return_value = FakeResponse(status=302)
        with self.assertRaisesRegex(IngestionError, "error HTTP"):
            fetch_api_source()

    @patch("crew_core.ingestion.requests.get")
    def test_non_json_content_is_rejected(self, get):
        get.return_value = FakeResponse(b"hello", content_type="text/plain")
        with self.assertRaisesRegex(IngestionError, "contenido JSON"):
            fetch_api_source()

    @patch("crew_core.ingestion.requests.get")
    def test_malformed_json_is_rejected(self, get):
        get.return_value = FakeResponse(b"{broken")
        with self.assertRaisesRegex(IngestionError, "JSON inválido"):
            fetch_api_source()

    @patch("crew_core.ingestion.requests.get")
    def test_oversized_response_is_rejected(self, get):
        get.return_value = FakeResponse(b"x" * (MAX_RESPONSE_BYTES + 1))
        with self.assertRaisesRegex(IngestionError, "demasiado grande"):
            fetch_api_source()

    def test_non_allowlisted_source_is_rejected_without_http(self):
        with patch("crew_core.ingestion.requests.get") as get:
            with self.assertRaisesRegex(IngestionError, "no permitida"):
                fetch_api_source("http://127.0.0.1/private")
            get.assert_not_called()


class IngestionRegistryTests(unittest.TestCase):
    def test_id_preserves_original_data_and_copy_isolated(self):
        clock = [10.0]
        registry = IngestionRegistry(clock=lambda: clock[0])
        original = {"id": 1, "title": "original"}
        record = registry.store("source", "Source", original)
        original["title"] = "alterado"
        self.assertNotEqual(record["ingestion_id"], "")
        self.assertEqual(registry.get(record["ingestion_id"])["data"]["title"], "original")

    def test_expired_id_is_removed(self):
        clock = [10.0]
        registry = IngestionRegistry(ttl_seconds=5, clock=lambda: clock[0])
        record = registry.store("source", "Source", {"id": 1})
        clock[0] = 15.0
        self.assertIsNone(registry.get(record["ingestion_id"]))

    def test_max_entries_evicts_oldest(self):
        clock = [1.0]
        registry = IngestionRegistry(max_entries=1, clock=lambda: clock[0])
        first = registry.store("one", "One", {"id": 1})
        clock[0] = 2.0
        registry.store("two", "Two", {"id": 2})
        self.assertIsNone(registry.get(first["ingestion_id"]))


class CrewInputTests(unittest.TestCase):
    def test_valid_manual_input_data(self):
        value = {"id": 1, "completed": False}
        self.assertIs(validate_input_data(value), value)

    def test_invalid_manual_input_data(self):
        with self.assertRaisesRegex(ValueError, "objeto o array"):
            validate_input_data("not-an-object")

    def test_oversized_manual_input_data(self):
        with self.assertRaisesRegex(ValueError, "excede"):
            validate_input_data({"value": "x" * (MAX_RESPONSE_BYTES + 1)})

    @patch("crew_core.runner.create_research_crew")
    def test_manual_runner_call_remains_compatible(self, create_crew):
        crew = Mock()
        expected = Mock()
        crew.kickoff.return_value = expected
        create_crew.return_value = crew
        self.assertIs(run_research_crew("tema manual"), expected)
        inputs = crew.kickoff.call_args.kwargs["inputs"]
        self.assertEqual(inputs["topic"], "tema manual")
        self.assertIn("No se proporcionaron", inputs["input_data"])

    def test_validation_status_extraction(self):
        extract = CrewRunRegistry._extract_validation_status
        self.assertEqual(extract("ok\nVALIDATION_STATUS: APPROVED"), "APPROVED")
        self.assertEqual(
            extract("VALIDATION_STATUS: NEEDS_REVISION"), "NEEDS_REVISION"
        )
        self.assertIsNone(extract("APPROVED"))


class RateLimitAndRetentionTests(unittest.TestCase):
    def test_rate_limit_allows_then_rejects_until_cooldown(self):
        clock = [100.0]
        limiter = CrewRunRateLimiter(cooldown_seconds=10, clock=lambda: clock[0])
        limiter.acquire()
        with self.assertRaises(CrewRunRateLimitError):
            limiter.acquire()
        clock[0] = 110.0
        limiter.acquire()

    def test_busy_admission_does_not_consume_cooldown(self):
        clock = [10.0]
        limiter = CrewRunRateLimiter(cooldown_seconds=10, clock=lambda: clock[0])
        registry = CrewRunRegistry(clock=lambda: clock[0])
        with patch.object(registry._executor, "submit"):
            with registry._lock:
                registry._runs["active"] = {
                    "status": "RUNNING",
                    "finished_at": None,
                }
            with self.assertRaises(CrewRunBusyError):
                registry.start("busy", rate_limiter=limiter)
            self.assertIsNone(limiter._last_started_at)
        registry._executor.shutdown(wait=True)

    def test_active_run_busy_does_not_extend_existing_cooldown(self):
        clock = [0.0]
        limiter = CrewRunRateLimiter(cooldown_seconds=10, clock=lambda: clock[0])
        registry = CrewRunRegistry(clock=lambda: clock[0])
        with patch.object(registry._executor, "submit"):
            registry.start("accepted", rate_limiter=limiter)
            clock[0] = 5.0
            with self.assertRaises(CrewRunBusyError):
                registry.start("busy", rate_limiter=limiter)
            self.assertEqual(limiter._last_started_at, 0.0)
        registry._executor.shutdown(wait=True)

    def test_cooldown_rejection_does_not_create_run(self):
        clock = [0.0]
        limiter = CrewRunRateLimiter(cooldown_seconds=10, clock=lambda: clock[0])
        registry = CrewRunRegistry(clock=lambda: clock[0])
        with patch.object(registry._executor, "submit"):
            first = registry.start("accepted", rate_limiter=limiter)
            with registry._lock:
                registry._runs[first["run_id"]]["status"] = "DONE"
                registry._runs[first["run_id"]]["finished_at"] = 0.0
            clock[0] = 1.0
            with self.assertRaises(CrewRunRateLimitError):
                registry.start("limited", rate_limiter=limiter)
            self.assertEqual(len(registry._runs), 1)
            self.assertEqual(limiter._last_started_at, 0.0)
        registry._executor.shutdown(wait=True)

    def test_accepted_run_consumes_cooldown(self):
        clock = [25.0]
        limiter = CrewRunRateLimiter(cooldown_seconds=10, clock=lambda: clock[0])
        registry = CrewRunRegistry(clock=lambda: clock[0])
        with patch.object(registry._executor, "submit"):
            run = registry.start("accepted", rate_limiter=limiter)
            self.assertEqual(run["status"], "RUNNING")
            self.assertEqual(limiter._last_started_at, 25.0)
        registry._executor.shutdown(wait=True)

    def test_concurrent_admission_creates_at_most_one_run(self):
        limiter = CrewRunRateLimiter(cooldown_seconds=10)
        registry = CrewRunRegistry()

        def attempt():
            try:
                return registry.start("concurrent", rate_limiter=limiter)["run_id"]
            except (CrewRunBusyError, CrewRunRateLimitError):
                return None

        with patch.object(registry._executor, "submit"):
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(lambda _: attempt(), range(2)))
            self.assertEqual(sum(result is not None for result in results), 1)
            self.assertEqual(len(registry._runs), 1)
        registry._executor.shutdown(wait=True)

    def test_completed_runs_are_purged_but_active_is_preserved(self):
        clock = [0.0]
        registry = CrewRunRegistry(retention_seconds=10, clock=lambda: clock[0])
        with patch.object(registry._executor, "submit"):
            old = registry.start("old")
            with registry._lock:
                registry._runs[old["run_id"]]["status"] = "DONE"
                registry._runs[old["run_id"]]["finished_at"] = 0.0
            clock[0] = 11.0
            active = registry.start("active")
            self.assertIsNone(registry.get(old["run_id"]))
            self.assertEqual(registry.get(active["run_id"])["status"], "RUNNING")
        registry._executor.shutdown(wait=True)

    def test_max_completed_history_is_enforced(self):
        registry = CrewRunRegistry(max_completed_runs=1)
        with registry._lock:
            registry._runs = {
                "old": {"status": "DONE", "finished_at": 1.0},
                "new": {"status": "ERROR", "finished_at": 2.0},
            }
            registry._purge_locked(2.0)
            self.assertNotIn("old", registry._runs)
            self.assertIn("new", registry._runs)
        registry._executor.shutdown(wait=True)


class FlaskHardeningTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"CREW_DASHBOARD_TOKEN": TOKEN})
        self.env.start()
        self.client = app_module.app.test_client()
        self.registry = Mock()
        self.registry.has_active.return_value = False
        self.registry.start.return_value = {
            "run_id": "run-1",
            "status": "RUNNING",
            "source_type": "manual",
            "source_name": None,
        }
        self.limiter = Mock()
        self.registry_patch = patch.object(app_module, "crew_run_registry", self.registry)
        self.limiter_patch = patch.object(app_module, "crew_run_rate_limiter", self.limiter)
        self.registry_patch.start()
        self.limiter_patch.start()

    def tearDown(self):
        self.limiter_patch.stop()
        self.registry_patch.stop()
        self.env.stop()

    def test_missing_token_returns_401(self):
        response = self.client.post("/api/crew/run", json={"topic": "test"})
        self.assertEqual(response.status_code, 401)
        self.registry.start.assert_not_called()

    def test_wrong_token_returns_401(self):
        response = self.client.post(
            "/api/crew/run",
            json={"topic": "test"},
            headers={"Authorization": "Bearer wrong"},
        )
        self.assertEqual(response.status_code, 401)

    def test_correct_token_allows_manual_run(self):
        response = self.client.post(
            "/api/crew/run", json={"topic": "test"}, headers=AUTH_HEADERS
        )
        self.assertEqual(response.status_code, 202)

    def test_rate_limit_returns_429(self):
        self.registry.start.side_effect = CrewRunRateLimitError(9)
        response = self.client.post(
            "/api/crew/run", json={"topic": "test"}, headers=AUTH_HEADERS
        )
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["Retry-After"], "9")
        self.assertIs(
            self.registry.start.call_args.kwargs["rate_limiter"], self.limiter
        )

    def test_busy_returns_409(self):
        self.registry.start.side_effect = CrewRunBusyError
        response = self.client.post(
            "/api/crew/run", json={"topic": "test"}, headers=AUTH_HEADERS
        )
        self.assertEqual(response.status_code, 409)
        self.limiter.acquire.assert_not_called()

    def test_manual_input_validation_at_endpoint(self):
        response = self.client.post(
            "/api/crew/run",
            json={"topic": "test", "input_data": "invalid"},
            headers=AUTH_HEADERS,
        )
        self.assertEqual(response.status_code, 400)

    def test_oversized_manual_input_is_rejected_at_endpoint(self):
        response = self.client.post(
            "/api/crew/run",
            json={"topic": "test", "input_data": {"value": "x" * (MAX_RESPONSE_BYTES + 1)}},
            headers=AUTH_HEADERS,
        )
        self.assertEqual(response.status_code, 400)
        self.registry.start.assert_not_called()

    def test_status_without_token_returns_401_without_lookup_or_content(self):
        self.registry.get.return_value = {
            "run_id": "existing-run",
            "research_output": "sensitive-output",
        }
        response = self.client.get("/api/crew/status/existing-run")
        self.assertEqual(response.status_code, 401)
        self.assertNotIn(b"sensitive-output", response.data)
        self.registry.get.assert_not_called()

    def test_status_with_wrong_token_returns_401_without_lookup(self):
        response = self.client.get(
            "/api/crew/status/existing-run",
            headers={"Authorization": "Bearer wrong"},
        )
        self.assertEqual(response.status_code, 401)
        self.registry.get.assert_not_called()

    def test_status_with_correct_token_and_existing_run_returns_200(self):
        self.registry.get.return_value = {
            "run_id": "existing-run",
            "status": "RUNNING",
        }
        response = self.client.get(
            "/api/crew/status/existing-run", headers=AUTH_HEADERS
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["run_id"], "existing-run")

    def test_status_with_correct_token_and_purged_run_returns_404(self):
        self.registry.get.return_value = None
        response = self.client.get(
            "/api/crew/status/purged-run", headers=AUTH_HEADERS
        )
        self.assertEqual(response.status_code, 404)


class DashboardStatusAuthTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dashboard = Path(app_module.BASE_DIR, "dashboard.html").read_text(
            encoding="utf-8"
        )
        start = cls.dashboard.index("async function pollCrewStatus()")
        end = cls.dashboard.index("async function ejecutarCrew()", start)
        cls.polling = cls.dashboard[start:end]

    def test_polling_sends_bearer_from_current_token_mechanism(self):
        self.assertIn('"Authorization":"Bearer "+crewToken()', self.polling)
        self.assertIn('sessionStorage.getItem("crew_dashboard_token")', self.dashboard)

    def test_polling_does_not_put_token_in_url_or_print_it(self):
        fetch_url = self.polling.split(",", 1)[0]
        self.assertNotIn("crewToken()", fetch_url)
        self.assertNotIn("console.", self.polling)

    def test_polling_handles_unauthorized_response_safely(self):
        self.assertIn("response.status===401", self.polling)
        self.assertIn("stopCrewPolling()", self.polling)
        self.assertIn("setCrewControlsRunning(false)", self.polling)


class RealSmokeStatusAuthTests(unittest.TestCase):
    def test_real_smoke_authenticates_status_polling(self):
        smoke = Path(
            app_module.BASE_DIR, "tests", "real_api_crew_smoke.py"
        ).read_text(encoding="utf-8")
        self.assertIn('os.getenv("CREW_DASHBOARD_TOKEN", "").strip()', smoke)
        self.assertIn(
            'client.get(started["status_url"], headers=headers)', smoke
        )


class FlaskIngestionIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"CREW_DASHBOARD_TOKEN": TOKEN})
        self.env.start()
        self.client = app_module.app.test_client()
        self.clock = [1.0]
        self.ingestions = IngestionRegistry(ttl_seconds=5, clock=lambda: self.clock[0])
        self.ingestion_patch = patch.object(
            app_module, "ingestion_registry", self.ingestions
        )
        self.ingestion_patch.start()

    def tearDown(self):
        self.ingestion_patch.stop()
        self.env.stop()

    def _create_ingestion(self):
        result = {
            "source": "jsonplaceholder_todo",
            "source_name": "JSONPlaceholder Todo",
            "status": "OK",
            "data": {"id": 1, "title": "original"},
            "preview": '{"id": 1, "title": "original"}',
        }
        with patch.object(app_module, "fetch_api_source", return_value=result):
            return self.client.post(
                "/api/ingestion/api",
                json={"source": "jsonplaceholder_todo"},
                headers=AUTH_HEADERS,
            )

    def test_ingestion_endpoint_generates_id_and_keeps_data_server_side(self):
        response = self._create_ingestion()
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertIn("ingestion_id", payload)
        self.assertNotIn("data", payload)
        record = self.ingestions.get(payload["ingestion_id"])
        self.assertEqual(record["data"]["title"], "original")

    def test_missing_ingestion_id_is_rejected(self):
        response = self.client.post(
            "/api/crew/run",
            json={"topic": "test", "source_type": "api", "ingestion_id": "missing"},
            headers=AUTH_HEADERS,
        )
        self.assertEqual(response.status_code, 400)

    def test_expired_ingestion_id_is_rejected(self):
        ingestion_id = self._create_ingestion().get_json()["ingestion_id"]
        self.clock[0] = 6.0
        response = self.client.post(
            "/api/crew/run",
            json={"topic": "test", "source_type": "api", "ingestion_id": ingestion_id},
            headers=AUTH_HEADERS,
        )
        self.assertEqual(response.status_code, 400)

    def test_browser_cannot_replace_api_data(self):
        ingestion_id = self._create_ingestion().get_json()["ingestion_id"]
        response = self.client.post(
            "/api/crew/run",
            json={
                "topic": "test",
                "source_type": "api",
                "ingestion_id": ingestion_id,
                "input_data": {"title": "manipulado"},
            },
            headers=AUTH_HEADERS,
        )
        self.assertEqual(response.status_code, 400)

    def test_run_uses_original_server_side_data(self):
        ingestion_id = self._create_ingestion().get_json()["ingestion_id"]
        run_registry = Mock()
        run_registry.has_active.return_value = False
        run_registry.start.return_value = {
            "run_id": "run-api",
            "status": "RUNNING",
            "source_type": "api",
            "source_name": "JSONPlaceholder Todo",
        }
        with (
            patch.object(app_module, "crew_run_registry", run_registry),
            patch.object(app_module, "crew_run_rate_limiter"),
        ):
            response = self.client.post(
                "/api/crew/run",
                json={"topic": "test", "source_type": "api", "ingestion_id": ingestion_id},
                headers=AUTH_HEADERS,
            )
        self.assertEqual(response.status_code, 202)
        self.assertEqual(
            run_registry.start.call_args.kwargs["input_data"],
            {"id": 1, "title": "original"},
        )


if __name__ == "__main__":
    unittest.main()
