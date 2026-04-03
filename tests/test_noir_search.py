import json
import unittest
from shutil import rmtree
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import noir_search

PROJECT_ROOT = Path(__file__).resolve().parents[1]
TEST_TEMP_ROOT = PROJECT_ROOT / ".tmp_tests"


@contextmanager
def project_temp_dir():
    TEST_TEMP_ROOT.mkdir(exist_ok=True)
    temp_dir = TEST_TEMP_ROOT / f"case_{uuid4().hex}"
    temp_dir.mkdir(parents=True, exist_ok=False)
    try:
        yield temp_dir
    finally:
        rmtree(temp_dir, ignore_errors=True)


class LoadQueriesTests(unittest.TestCase):
    def test_load_queries_ignores_comments_and_blank_lines(self):
        with project_temp_dir() as temp_dir:
            queries_file = temp_dir / "queries.txt"
            queries_file.write_text(
                "# comentario\n\nPython\n  Selenium  \n# outro comentario\nEdge\n",
                encoding="utf-8",
            )

            with patch("noir_search.random.shuffle", side_effect=lambda items: None):
                queries = noir_search.load_queries(queries_file)

            self.assertEqual(["Python", "Selenium", "Edge"], queries)

    def test_load_queries_returns_defaults_when_file_is_none(self):
        with patch("noir_search.random.shuffle", side_effect=lambda items: None):
            self.assertEqual(
                noir_search.DEFAULT_QUERIES,
                noir_search.load_queries(None),
            )

    def test_refresh_local_queries_file_removes_duplicates_and_saves_file(self):
        with project_temp_dir() as temp_dir:
            queries_file = temp_dir / "queries.txt"
            queries_file.write_text(
                "# comentario\nPython\nSelenium\npython\n  Selenium  \nEdge\n",
                encoding="utf-8",
            )

            with patch("noir_search.random.shuffle", side_effect=lambda items: items.reverse()):
                queries = noir_search.refresh_local_queries_file(queries_file)

            self.assertEqual(["Edge", "Selenium", "Python"], queries)
            self.assertEqual("Edge\nSelenium\nPython\n", queries_file.read_text(encoding="utf-8"))


class ConfigTests(unittest.TestCase):
    def test_build_config_reads_json_and_resolves_relative_paths(self):
        with project_temp_dir() as temp_dir:
            runtime_base = temp_dir
            resource_base = runtime_base / "bundle"
            resource_base.mkdir()

            config_file = runtime_base / "config.json"
            config_file.write_text(
                json.dumps(
                    {
                        "queries_file": "data/queries.txt",
                        "delay_seconds": 1.5,
                        "keep_open_seconds": 2,
                        "timeout_seconds": 9,
                        "start_url": "https://example.com",
                        "headless": True,
                        "log_file": "logs/custom.log",
                    }
                ),
                encoding="utf-8",
            )

            args = noir_search.parse_args(["--config", str(config_file)])
            config = noir_search.build_config(args, runtime_base, resource_base)

            self.assertEqual((runtime_base / "data" / "queries.txt").resolve(), config.queries_file)
            self.assertEqual(1.5, config.delay_seconds)
            self.assertEqual(2.0, config.keep_open_seconds)
            self.assertEqual(9, config.timeout_seconds)
            self.assertEqual("https://example.com", config.start_url)
            self.assertTrue(config.headless)
            self.assertEqual((runtime_base / "logs" / "custom.log").resolve(), config.log_file)

    def test_build_config_prefers_cli_overrides(self):
        with project_temp_dir() as temp_dir:
            runtime_base = temp_dir
            resource_base = runtime_base / "bundle"
            resource_base.mkdir()

            config_file = runtime_base / "config.json"
            config_file.write_text(
                json.dumps(
                    {
                        "delay_seconds": 1,
                        "headless": True,
                        "start_url": "https://example.com",
                    }
                ),
                encoding="utf-8",
            )

            args = noir_search.parse_args(
                [
                    "--config",
                    str(config_file),
                    "--delay",
                    "4",
                    "--show-browser",
                    "--start-url",
                    "https://www.bing.com",
                ]
            )
            config = noir_search.build_config(args, runtime_base, resource_base)

            self.assertEqual(4.0, config.delay_seconds)
            self.assertFalse(config.headless)
            self.assertEqual("https://www.bing.com", config.start_url)

    def test_build_config_uses_runtime_queries_file_when_present(self):
        with project_temp_dir() as temp_dir:
            runtime_base = temp_dir
            resource_base = runtime_base / "bundle"
            resource_base.mkdir()

            runtime_queries = runtime_base / "queries.txt"
            runtime_queries.write_text("Python\n", encoding="utf-8")

            args = noir_search.parse_args([])
            config = noir_search.build_config(args, runtime_base, resource_base)

            self.assertEqual(runtime_queries, config.queries_file)


if __name__ == "__main__":
    unittest.main()
