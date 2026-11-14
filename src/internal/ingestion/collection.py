"""Retain original Codex log lines and replay committed records."""

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import re
import sqlite3
from uuid import uuid4

from internal.ingestion.parser import Diagnostic, discover_files, read_source_lines
from internal.paths import DATA_DIR


@dataclass(frozen=True)
class SourceLine:
    """A line read from a source with its position and original bytes."""

    source_path: str
    line_number: int
    original_line_bytes: bytes


@dataclass(frozen=True)
class CollectedCodexRecord:
    """An original line and its stable collection provenance."""

    record_id: str
    log_identity: str
    source_path: str
    line_number: int
    original_line_bytes: bytes
    collected_at: str


def _identifier(value: str) -> str:
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", value):
        raise ValueError(f"Invalid SQLite identifier: {value!r}")
    return f'"{value}"'


class DatabaseWriter:
    """Write mapped rows to SQLite under caller-controlled transactions."""

    def __init__(self, database_path: Path = DATA_DIR / "codex_usage.sqlite3"):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        with self.transaction():
            version = self.connection.execute("PRAGMA user_version").fetchone()[0]
            if version > 6:
                raise ValueError(f"Unsupported database schema version: {version}")
            if version == 0:
                self.connection.execute("CREATE TABLE IF NOT EXISTS logs (log_identity TEXT PRIMARY KEY)")
                self.connection.execute(
                    "CREATE TABLE IF NOT EXISTS source_paths ("
                    "source_path TEXT PRIMARY KEY, log_identity TEXT NOT NULL REFERENCES logs(log_identity))"
                )
                self.connection.execute(
                    "CREATE TABLE IF NOT EXISTS collected_records ("
                    "record_id TEXT PRIMARY KEY, log_identity TEXT NOT NULL REFERENCES logs(log_identity), "
                    "source_path TEXT NOT NULL, line_number INTEGER NOT NULL, "
                    "original_line_bytes BLOB NOT NULL, collected_at TEXT NOT NULL, "
                    "UNIQUE(log_identity, line_number))"
                )
                self.connection.execute("PRAGMA user_version = 1")
                version = 1
            if version == 1:
                self.connection.execute(
                    "CREATE TABLE IF NOT EXISTS agent_threads ("
                    "execution_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, thread_id TEXT NOT NULL, "
                    "parent_execution_id TEXT, agent_name TEXT, role TEXT, nickname TEXT)"
                )
                self.connection.execute(
                    "CREATE TABLE IF NOT EXISTS usage_records ("
                    "usage_id TEXT PRIMARY KEY, source_record_id TEXT NOT NULL REFERENCES collected_records(record_id), "
                    "execution_id TEXT REFERENCES agent_threads(execution_id), observed_at TEXT, prior_observed_at TEXT, "
                    "source_working_directory TEXT, project_key TEXT, project_label TEXT, model TEXT, "
                    "input_tokens INTEGER, output_tokens INTEGER, cached_input_tokens INTEGER, "
                    "cache_write_input_tokens INTEGER, reasoning_output_tokens INTEGER, total_tokens INTEGER, "
                    "non_cached_input_tokens INTEGER, coverage TEXT NOT NULL, counter_provenance TEXT NOT NULL)"
                )
                self.connection.execute(
                    "CREATE TABLE IF NOT EXISTS coverage_diagnostics ("
                    "source_record_id TEXT, execution_id TEXT, observed_at TEXT, message TEXT NOT NULL)"
                )
                self.connection.execute("PRAGMA user_version = 2")
                version = 2
            if version == 2:
                self.connection.execute(
                    "CREATE TABLE IF NOT EXISTS time_markers ("
                    "marker_id TEXT PRIMARY KEY, name TEXT NOT NULL, timestamp TEXT NOT NULL)"
                )
                self.connection.execute(
                    "CREATE TABLE IF NOT EXISTS import_state (id INTEGER PRIMARY KEY CHECK (id = 1), "
                    "initialized INTEGER NOT NULL)"
                )
                self.connection.execute("PRAGMA user_version = 3")
                version = 3
            if version == 3:
                self.connection.execute("ALTER TABLE coverage_diagnostics ADD COLUMN kind TEXT NOT NULL DEFAULT 'usage'")
                self.connection.execute("PRAGMA user_version = 4")
                version = 4
            if version == 4:
                self.connection.execute(
                    "CREATE TABLE published_logs (log_identity TEXT PRIMARY KEY REFERENCES logs(log_identity), "
                    "last_line INTEGER NOT NULL, last_length INTEGER NOT NULL, last_digest TEXT NOT NULL)"
                )
                self.connection.execute("ALTER TABLE import_state ADD COLUMN needs_rebuild INTEGER NOT NULL DEFAULT 0")
                self.connection.execute("UPDATE import_state SET initialized = 0, needs_rebuild = 1 WHERE initialized = 1")
                prior_rows = self.connection.execute(
                    "SELECT EXISTS(SELECT 1 FROM usage_records) OR EXISTS(SELECT 1 FROM agent_threads)"
                ).fetchone()[0]
                if prior_rows:
                    self.connection.execute(
                        "INSERT INTO import_state (id, initialized, needs_rebuild) VALUES (1, 0, 1) "
                        "ON CONFLICT(id) DO NOTHING"
                    )
                self.connection.execute("PRAGMA user_version = 5")
                version = 5
            if version == 5:
                self.connection.execute("ALTER TABLE time_markers ADD COLUMN session_ids TEXT")
                self.connection.execute("PRAGMA user_version = 6")

    @contextmanager
    def transaction(self):
        """Commit all enclosed writes together or roll them back on failure."""
        self.connection.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.connection.commit()
        except BaseException:
            self.connection.rollback()
            raise

    def write(self, table: str, mapping: dict[str, str], rows, conflict_columns=()):
        """Write dictionaries using destination-to-source column mappings.

        Args:
            table: Destination table name.
            mapping: Destination column names mapped to keys in each row.
            rows: Iterable of source dictionaries.
            conflict_columns: Destination columns identifying an upsert conflict.
        """
        if not mapping or any(column not in mapping for column in conflict_columns):
            raise ValueError("Destination mapping and conflict columns must be valid.")
        columns = list(mapping)
        sql = f"INSERT INTO {_identifier(table)} ({', '.join(_identifier(c) for c in columns)}) "
        sql += f"VALUES ({', '.join('?' for _ in columns)})"
        if conflict_columns:
            targets = ", ".join(_identifier(c) for c in conflict_columns)
            updates = [c for c in columns if c not in conflict_columns]
            if updates:
                assignments = ", ".join(f"{_identifier(c)} = excluded.{_identifier(c)}" for c in updates)
                sql += f" ON CONFLICT ({targets}) DO UPDATE SET {assignments}"
            else:
                sql += f" ON CONFLICT ({targets}) DO NOTHING"
        self.connection.executemany(sql, (tuple(row[mapping[c]] for c in columns) for row in rows))

    def close(self):
        """Close the SQLite connection."""
        self.connection.close()


class CodexLogReader:
    """Discover log files and read source or committed replay lines."""

    def discover(self, roots: list[Path], diagnostics: list[Diagnostic]) -> list[Path]:
        """Discover source files while reporting inaccessible directories."""
        return discover_files(roots, diagnostics)

    def read_source(self, path: Path) -> list[SourceLine]:
        """Read positioned lines with their original bytes."""
        return [SourceLine(str(path.resolve()), number, line)
                for number, line in enumerate(read_source_lines(path), 1)]

    def replay(self, connection: sqlite3.Connection) -> list[CollectedCodexRecord]:
        """Read one ordered snapshot of committed records for rebuilding."""
        rows = connection.execute(
            "SELECT record_id, log_identity, source_path, line_number, original_line_bytes, collected_at "
            "FROM collected_records ORDER BY log_identity, line_number"
        ).fetchall()
        return [CollectedCodexRecord(*row) for row in rows]

    def replay_publication(self, connection: sqlite3.Connection) -> list[CollectedCodexRecord]:
        """Read exactly the raw evidence included in the current publication.

        The caller must hold a read transaction while loading the manifest and
        derived rows so every part of the report sees the same publication.
        """
        manifests = connection.execute(
            "SELECT log_identity, last_line, last_length, last_digest FROM published_logs ORDER BY log_identity"
        ).fetchall()
        records = []
        for log_id, last_line, last_length, digest in manifests:
            rows = connection.execute(
                "SELECT record_id, log_identity, source_path, line_number, original_line_bytes, collected_at "
                "FROM collected_records WHERE log_identity = ? AND line_number <= ? ORDER BY line_number",
                (log_id, last_line),
            ).fetchall()
            if len(rows) != last_line or any(row[3] != index for index, row in enumerate(rows, 1)):
                raise ValueError(f"Published source {log_id} has missing lines.")
            final = rows[-1]
            prefix = final[4][:last_length]
            if len(prefix) != last_length or hashlib.sha256(prefix).hexdigest() != digest:
                raise ValueError(f"Published source {log_id} no longer has its recorded byte prefix.")
            records.extend(CollectedCodexRecord(*row) for row in rows[:-1])
            records.append(CollectedCodexRecord(*final[:4], prefix, final[5]))
        return records


def _archive_key(path: str) -> tuple[str, str, str] | None:
    parts = Path(path).parts
    filename = Path(path).name.casefold()
    if not re.fullmatch(
        r"rollout-\d{4}-\d{2}-\d{2}t\d{2}-\d{2}-\d{2}-"
        r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.jsonl",
        filename,
    ):
        return None
    for index, part in enumerate(parts):
        if part.casefold() in {"sessions", "archived_sessions"}:
            return (str(Path(*parts[:index])).casefold(), part.casefold(), filename)
    return None


def _continues(stored: list[bytes], current: list[bytes]) -> bool:
    if len(current) < len(stored):
        return False
    for index, previous in enumerate(stored):
        line = current[index]
        if line == previous:
            continue
        if index != len(stored) - 1 or previous.endswith(b"\n") or not line.startswith(previous):
            return False
    return True


class CodexLogImporter:
    """Collect source files transactionally into a local raw-record store."""

    def __init__(self, reader: CodexLogReader, writer: DatabaseWriter, transformations=None):
        self.reader = reader
        self.writer = writer
        if transformations is None:
            from internal.ingestion.transformations import AgentThreadTransformation, UsageTransformation
            transformations = (AgentThreadTransformation(), UsageTransformation())
        self.transformations = tuple(transformations)
        if not self.transformations:
            raise ValueError("At least one transformation is required.")

    def collect(self, roots: list[Path]) -> list[Diagnostic]:
        """Collect each available source, returning read and write diagnostics."""
        diagnostics: list[Diagnostic] = []
        for path in self.reader.discover(roots, diagnostics):
            try:
                warning = self._collect_source(path)
                if warning:
                    diagnostics.append(Diagnostic(str(path), None, warning))
            except (OSError, sqlite3.Error, ValueError) as exc:
                diagnostics.append(Diagnostic(str(path), None, f"Cannot collect source: {exc}", fatal=True))
        return diagnostics

    def _collect_source(self, path: Path) -> str | None:
        source_path = str(path.resolve())
        connection = self.writer.connection
        warning = None
        with self.writer.transaction():
            lines = [line.original_line_bytes for line in self.reader.read_source(path)]
            existing = connection.execute(
                "SELECT log_identity FROM source_paths WHERE source_path = ?", (source_path,)
            ).fetchone()
            log_id = existing[0] if existing else None
            stored = self._lines(log_id) if log_id else []
            if log_id and not _continues(stored, lines):
                warning = "Source bytes changed or were truncated; retained as a separate log."
                log_id, stored = None, []
            if not log_id and not existing and lines:
                key = _archive_key(source_path)
                candidates = connection.execute(
                    "SELECT source_path, log_identity FROM source_paths "
                    "UNION SELECT DISTINCT source_path, log_identity FROM collected_records"
                ).fetchall()
                matches = set()
                unresolved = False
                for candidate_path, candidate_id in candidates:
                    candidate_key = _archive_key(candidate_path)
                    if (key is None or candidate_key is None or key[0] != candidate_key[0]
                            or key[1] == candidate_key[1] or key[2] != candidate_key[2]):
                        continue
                    candidate_lines = self._lines(candidate_id)
                    if candidate_lines and _continues(candidate_lines, lines):
                        matches.add(candidate_id)
                    elif candidate_lines:
                        unresolved = True
                if len(matches) == 1:
                    log_id = matches.pop()
                    stored = self._lines(log_id)
                elif len(matches) > 1:
                    warning = "Multiple archive candidates match; retained as a separate log."
                elif unresolved:
                    warning = "Source differs from an archive candidate; retained as a separate log."
            if not log_id:
                log_id = str(uuid4())
                self.writer.write("logs", {"log_identity": "log_identity"}, [{"log_identity": log_id}])
            self.writer.write("source_paths", {"source_path": "source_path", "log_identity": "log_identity"},
                              [{"source_path": source_path, "log_identity": log_id}], ("source_path",))
            if stored and stored[-1] != lines[len(stored) - 1]:
                connection.execute("UPDATE collected_records SET original_line_bytes = ? WHERE log_identity = ? AND line_number = ?",
                                   (lines[len(stored) - 1], log_id, len(stored)))
            timestamp = datetime.now(timezone.utc).isoformat()
            records = [CollectedCodexRecord(str(uuid4()), log_id, source_path, number, line, timestamp)
                       for number, line in enumerate(lines[len(stored):], len(stored) + 1)]
            columns = ("record_id", "log_identity", "source_path", "line_number", "original_line_bytes", "collected_at")
            self.writer.write("collected_records", {column: column for column in columns},
                              (asdict(record) for record in records))
        return warning

    def _lines(self, log_id: str) -> list[bytes]:
        rows = self.writer.connection.execute(
            "SELECT original_line_bytes FROM collected_records WHERE log_identity = ? ORDER BY line_number", (log_id,)
        )
        return [row[0] for row in rows]

    def refresh(self, roots: list[Path]) -> tuple[bool, list[Diagnostic]]:
        """Collect sources and publish a rebuild only after successful collection."""
        diagnostics = self.collect(roots)
        if any(item.fatal for item in diagnostics):
            return False, diagnostics
        success, rebuild_diagnostics = self.rebuild()
        return success, diagnostics + rebuild_diagnostics

    def rebuild(self) -> tuple[bool, list[Diagnostic]]:
        """Atomically publish transformations from a committed raw snapshot."""
        connection = self.writer.connection
        try:
            with self.writer.transaction():
                connection.execute("PRAGMA defer_foreign_keys = ON")
                records = self.reader.replay(connection)
                outputs = []
                coverage = []
                for transformation in self.transformations:
                    rows, diagnostics = transformation.transform(records)
                    rows = list(rows)
                    if not all(isinstance(row, transformation.record_type) for row in rows):
                        raise TypeError("Transformation returned an unexpected record type.")
                    table, mapping = transformation.destination
                    outputs.append((table, mapping, [asdict(row) for row in rows]))
                    coverage.extend({**item, "kind": "hierarchy" if table == "agent_threads" else "usage"}
                                    for item in diagnostics)
                for table, _, _ in reversed(outputs):
                    connection.execute(f"DELETE FROM {_identifier(table)}")
                connection.execute("DELETE FROM coverage_diagnostics")
                for table, mapping, rows in outputs:
                    self.writer.write(table, mapping, rows)
                columns = ("source_record_id", "execution_id", "observed_at", "message", "kind")
                self.writer.write("coverage_diagnostics", {column: column for column in columns}, coverage)
                last_records = {record.log_identity: record for record in records}
                manifests = [{"log_identity": record.log_identity, "last_line": record.line_number,
                              "last_length": len(record.original_line_bytes),
                              "last_digest": hashlib.sha256(record.original_line_bytes).hexdigest()}
                             for record in last_records.values()]
                connection.execute("DELETE FROM published_logs")
                manifest_columns = ("log_identity", "last_line", "last_length", "last_digest")
                self.writer.write("published_logs", {column: column for column in manifest_columns}, manifests)
                self.writer.write("import_state", {"id": "id", "initialized": "initialized", "needs_rebuild": "needs_rebuild"},
                                  [{"id": 1, "initialized": 1, "needs_rebuild": 0}], ("id",))
            return True, []
        except Exception as exc:
            return False, [Diagnostic(str(self.writer.database_path), None, f"Cannot rebuild usage: {exc}", fatal=True)]
