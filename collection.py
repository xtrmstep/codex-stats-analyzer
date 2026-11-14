"""Retain original Codex log lines and replay committed records."""

from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
import sqlite3
from uuid import uuid4

from parser import Diagnostic, discover_files, read_source_lines


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

    def __init__(self, database_path: Path = Path(__file__).resolve().parent / "data" / "codex_usage.sqlite3"):
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.database_path)
        self.connection.execute("PRAGMA foreign_keys = ON")
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        version = self.connection.execute("PRAGMA user_version").fetchone()[0]
        if version > 1:
            raise ValueError(f"Unsupported database schema version: {version}")
        if version == 0:
            with self.connection:
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


def _archive_key(path: str) -> tuple[str, str] | None:
    parts = Path(path).parts
    for index, part in enumerate(parts):
        if part.casefold() in {"sessions", "archived_sessions"}:
            return (str(Path(*parts[:index])).casefold(), str(Path(*parts[index + 1:])).casefold())
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

    def __init__(self, reader: CodexLogReader, writer: DatabaseWriter, transformations=()):
        self.reader = reader
        self.writer = writer
        self.transformations = tuple(transformations)

    def collect(self, roots: list[Path]) -> list[Diagnostic]:
        """Collect each available source, returning read and write diagnostics."""
        diagnostics: list[Diagnostic] = []
        for path in self.reader.discover(roots, diagnostics):
            try:
                self._collect_source(path)
            except (OSError, sqlite3.Error, ValueError) as exc:
                diagnostics.append(Diagnostic(str(path), None, f"Cannot collect source: {exc}"))
        return diagnostics

    def _collect_source(self, path: Path) -> None:
        source_path = str(path.resolve())
        connection = self.writer.connection
        with self.writer.transaction():
            lines = [line.original_line_bytes for line in self.reader.read_source(path)]
            existing = connection.execute(
                "SELECT log_identity FROM source_paths WHERE source_path = ?", (source_path,)
            ).fetchone()
            log_id = existing[0] if existing else None
            stored = self._lines(log_id) if log_id else []
            if log_id and not _continues(stored, lines):
                log_id, stored = None, []
            if not log_id and not existing and lines:
                key = _archive_key(source_path)
                candidates = connection.execute(
                    "SELECT source_path, log_identity FROM source_paths "
                    "UNION SELECT DISTINCT source_path, log_identity FROM collected_records"
                ).fetchall()
                matches = {candidate_id for candidate_path, candidate_id in candidates
                           if key is not None and _archive_key(candidate_path) == key
                           and candidate_path.casefold() != source_path.casefold()
                           and _continues(self._lines(candidate_id), lines)
                           and self._lines(candidate_id)}
                if len(matches) == 1:
                    log_id = matches.pop()
                    stored = self._lines(log_id)
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

    def _lines(self, log_id: str) -> list[bytes]:
        rows = self.writer.connection.execute(
            "SELECT original_line_bytes FROM collected_records WHERE log_identity = ? ORDER BY line_number", (log_id,)
        )
        return [row[0] for row in rows]
