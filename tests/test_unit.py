"""Offline unit tests: these do not require MariaDB, Ollama, or model downloads."""

from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from embed import EMBEDDING_DIMENSION, vector_to_text  # noqa: E402
import index_data  # noqa: E402
from index_data import load_documents  # noqa: E402
from rag import build_prompt  # noqa: E402
from evaluate import hit_at_k  # noqa: E402


class FakeCursor:
    def __init__(self, state):
        self.state = state
        self.pending_row = None
        self.closed = False

    def execute(self, statement, parameters):
        normalized = " ".join(statement.split()).upper()
        if normalized.startswith("SELECT ID FROM DOCUMENTS"):
            self.pending_row = None
            for row in self.state["rows"]:
                if row["title"] == parameters[0] and row["source"] == parameters[1]:
                    self.pending_row = (row["id"],)
                    break
        elif normalized.startswith("UPDATE DOCUMENTS"):
            category, content, vector_text, document_id = parameters
            for row in self.state["rows"]:
                if row["id"] == document_id:
                    row.update(category=category, content=content, embedding=vector_text)
                    break
        elif normalized.startswith("INSERT INTO DOCUMENTS"):
            title, source, category, content, vector_text = parameters
            new_id = len(self.state["rows"]) + 1
            self.state["rows"].append(
                {
                    "id": new_id,
                    "title": title,
                    "source": source,
                    "category": category,
                    "content": content,
                    "embedding": vector_text,
                }
            )
        else:
            raise AssertionError(f"Unexpected SQL in unit test: {statement}")

    def fetchone(self):
        return self.pending_row

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, state):
        self.state = state
        self.commits = 0
        self.rollbacks = 0
        self.closed = False

    def cursor(self):
        return FakeCursor(self.state)

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


class EmbeddingUtilityTests(unittest.TestCase):
    def test_vector_to_text_serializes_384_values(self):
        serialized = vector_to_text([0.0] * EMBEDDING_DIMENSION)
        self.assertTrue(serialized.startswith("["))
        self.assertTrue(serialized.endswith("]"))
        self.assertEqual(len(json.loads(serialized)), 384)

    def test_vector_to_text_rejects_wrong_dimension(self):
        with self.assertRaises(ValueError):
            vector_to_text([0.1, 0.2, 0.3])

    def test_vector_to_text_rejects_non_finite_number(self):
        with self.assertRaises(ValueError):
            vector_to_text([float("nan")] + [0.0] * 383)


class DatasetTests(unittest.TestCase):
    def test_load_documents_validates_and_normalizes(self):
        payload = [
            {
                "title": "  A title  ",
                "source": "  class notes  ",
                "category": "  Databases  ",
                "content": "  Some content.  ",
            }
        ]
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "documents.json"
            file_path.write_text(json.dumps(payload), encoding="utf-8")
            result = load_documents(file_path)

        self.assertEqual(result[0]["title"], "A title")
        self.assertEqual(result[0]["source"], "class notes")
        self.assertEqual(result[0]["category"], "Databases")
        self.assertEqual(result[0]["content"], "Some content.")


    def test_reindexing_updates_existing_rows_instead_of_duplicating(self):
        state = {"rows": []}
        connections = []

        def connect():
            connection = FakeConnection(state)
            connections.append(connection)
            return connection

        fake_db = types.ModuleType("db")
        fake_db.get_connection = connect
        dataset = [
            {
                "title": "Mutual Exclusion",
                "source": "CS Knowledge Base",
                "category": "Operating Systems",
                "content": "Only one process uses the resource at a time.",
            }
        ]

        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "documents.json"
            file_path.write_text(json.dumps(dataset), encoding="utf-8")
            with patch.dict("sys.modules", {"db": fake_db}):
                with patch.object(
                    index_data, "embed_texts",
                    side_effect=lambda texts: [[0.0] * EMBEDDING_DIMENSION for _ in texts],
                ):
                    first = index_data.index_documents(file_path)
                    second = index_data.index_documents(file_path)

        self.assertEqual(first, {"inserted": 1, "updated": 0, "total": 1})
        self.assertEqual(second, {"inserted": 0, "updated": 1, "total": 1})
        self.assertEqual(len(state["rows"]), 1)
        self.assertEqual(len(connections), 2)
        self.assertEqual([connection.commits for connection in connections], [1, 1])
        self.assertTrue(all(connection.closed for connection in connections))

    def test_load_documents_rejects_duplicate_natural_key(self):
        item = {
            "title": "Same title",
            "source": "same source",
            "category": "Databases",
            "content": "Content",
        }
        with tempfile.TemporaryDirectory() as directory:
            file_path = Path(directory) / "documents.json"
            file_path.write_text(json.dumps([item, item]), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_documents(file_path)


class RagAndEvaluationTests(unittest.TestCase):
    def test_prompt_contains_question_and_retrieved_context(self):
        rows = [(1, "SQL Joins", "Databases", "Joins combine rows.", 0.12)]
        prompt = build_prompt("What are joins?", rows)
        self.assertIn("What are joins?", prompt)
        self.assertIn("SQL Joins", prompt)
        self.assertIn("Joins combine rows.", prompt)

    def test_hit_at_k_checks_only_the_first_k_rows(self):
        rows = [
            (1, "A", "Networking", "...", 0.1),
            (2, "B", "Databases", "...", 0.2),
            (3, "C", "Algorithms", "...", 0.3),
        ]
        self.assertFalse(hit_at_k(rows, {"Databases"}, 1))
        self.assertTrue(hit_at_k(rows, {"Databases"}, 2))


if __name__ == "__main__":
    unittest.main()
