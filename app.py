"""Local application entry point and configuration validation."""

from pathlib import Path
import os
import re
import sys
import tomllib

PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_DIR / "config.toml"


def load_source_directories(config_path: Path = CONFIG_PATH) -> list[Path]:
    """Load configured source directories, expanding Windows environment variables.

    Args:
        config_path: TOML configuration file to read.

    Returns:
        Configured source paths in order.

    Raises:
        ValueError: If the file or its source directory settings are invalid.
    """
    try:
        with config_path.open("rb") as config_file:
            config = tomllib.load(config_file)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(f"Cannot read {config_path}: {exc}") from exc

    sources = config.get("sources")
    if not isinstance(sources, dict):
        raise ValueError("config.toml must contain a [sources] section.")
    paths = sources.get("directories")
    if not isinstance(paths, list) or not paths:
        raise ValueError("sources.directories must be a non-empty list of paths.")

    resolved = []
    for path in paths:
        if not isinstance(path, str) or not path.strip():
            raise ValueError("Every sources.directories entry must be a non-empty string.")

        def expand_variable(match: re.Match[str]) -> str:
            name = match.group(1)
            value = os.environ.get(name)
            if value is None:
                raise ValueError(f"Environment variable %{name}% is not set for source path {path!r}.")
            return value

        expanded = re.sub(r"%([^%]+)%", expand_variable, path)
        if "%" in expanded:
            raise ValueError(f"Invalid environment variable in source path {path!r}.")
        source = Path(expanded).expanduser()
        if not source.is_absolute():
            source = PROJECT_DIR / source
        resolved.append(source)
    return resolved


def main() -> None:
    """Display the foundation screen or an actionable configuration error."""
    import streamlit as st

    st.set_page_config(page_title="Codex Usage Analyzer")
    st.title("Codex Usage Analyzer")
    try:
        sources = load_source_directories()
    except ValueError as exc:
        st.error(f"Configuration error: {exc} Edit config.toml and restart the application.")
        return
    from dashboard import render

    render(sources)


if __name__ == "__main__":
    if "--check-config" in sys.argv:
        try:
            for directory in load_source_directories():
                print(directory)
        except ValueError as exc:
            print(f"Configuration error: {exc} Edit config.toml and try again.", file=sys.stderr)
            sys.exit(1)
    else:
        main()

