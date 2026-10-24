"""Small JSON and TXT persistence helpers for the hotel application.

This module keeps file handling in one place so the guest and later management
classes do not need to repeat path, encoding, or error-handling code.
"""

from __future__ import annotations

# Used to convert Python data to JSON and JSON text back into Python data.
import json

# Makes it easier to work with file and folder paths on different systems.
from pathlib import Path

# Allows the helper to accept any JSON-compatible starting value.
from typing import Any


class FileManagerError(Exception):
    """Explain a data-file problem in a way the application can report."""


class FileManager:
    """Handle the application's simple JSON and TXT file operations.

    A FileManager is given one data directory and performs all reads and
    writes inside that directory. It does not decide hotel business rules.
    """

    def __init__(self, data_directory: str | Path = "data") -> None:
        """Set the data folder and create it if it is missing.

        ``self`` refers to the particular FileManager object being created.
        Keeping the directory on the object lets every method use the same
        location without repeating it as an argument.
        """
        self.data_directory = Path(data_directory)
        self.data_directory.mkdir(parents=True, exist_ok=True)

    def file_exists(self, filename: str) -> bool:
        """Return whether a named data file already exists.

        Parameters:
            filename: Name of a file inside the configured data directory.
        """
        return self._path_for(filename).exists()

    def initialize_json_file(self, filename: str, initial_data: Any) -> Path:
        """Create a JSON file only when it does not already exist.

        Existing data is deliberately left alone so application startup or a
        Streamlit rerun cannot replace records saved by the user.
        """
        path = self._path_for(filename)
        if not path.exists():
            self.save_json(filename, initial_data)
        return path

    def initialize_text_file(self, filename: str) -> Path:
        """Create an empty TXT file only when it does not already exist.

        Raises:
            FileManagerError: If the empty file cannot be created.
        """
        path = self._path_for(filename)
        if not path.exists():
            try:
                path.touch()
            except OSError as error:
                raise FileManagerError(
                    f"Could not initialize data file '{path}': {error}"
                ) from error
        return path

    def load_json(self, filename: str) -> Any:
        """Load JSON data from a file.

        Raises:
            FileManagerError: If the file is missing, malformed, or unreadable.
        """
        path = self._path_for(filename)
        try:
            with path.open("r", encoding="utf-8") as data_file:
                return json.load(data_file)
        except FileNotFoundError as error:
            raise FileManagerError(
                f"Data file '{path}' does not exist. Initialize it before loading."
            ) from error
        except json.JSONDecodeError as error:
            raise FileManagerError(
                f"Data file '{path}' contains malformed JSON: {error.msg}."
            ) from error
        except OSError as error:
            raise FileManagerError(
                f"Could not read data file '{path}': {error}"
            ) from error

    def save_json(self, filename: str, data: Any) -> Path:
        """Save JSON data to the named file.

        ``json.dump`` converts dictionaries and lists into readable structured
        JSON. Only the explicitly named file is replaced; other data files are
        not touched.

        Raises:
            FileManagerError: If the data cannot be serialized or saved.
        """
        path = self._path_for(filename)
        try:
            with path.open("w", encoding="utf-8") as data_file:
                json.dump(data, data_file, indent=2)
                data_file.write("\n")
        except (OSError, TypeError, ValueError) as error:
            raise FileManagerError(
                f"Could not save data file '{path}': {error}"
            ) from error
        return path

    def append_text(self, filename: str, record: str) -> Path:
        """Append one text record without replacing existing history.

        Append mode is important for ``history.txt`` because completed stays
        must remain available after later records are added.

        Raises:
            FileManagerError: If the record cannot be appended.
        """
        path = self._path_for(filename)
        try:
            with path.open("a", encoding="utf-8") as text_file:
                text_file.write(record)
        except OSError as error:
            raise FileManagerError(
                f"Could not append to data file '{path}': {error}"
            ) from error
        return path

    def read_text(self, filename: str) -> str:
        """Read a TXT data file as UTF-8 text.

        Raises:
            FileManagerError: If the file is missing or cannot be read.
        """
        path = self._path_for(filename)
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError as error:
            raise FileManagerError(
                f"Data file '{path}' does not exist. Initialize it before reading."
            ) from error
        except OSError as error:
            raise FileManagerError(
                f"Could not read data file '{path}': {error}"
            ) from error

    def _path_for(self, filename: str) -> Path:
        """Return a safe path inside the configured data directory.

        Rejecting nested paths keeps this beginner-level persistence helper
        focused on the known application files and prevents accidental writes
        elsewhere in the project.
        """
        path = self.data_directory / filename
        if path.parent != self.data_directory:
            raise FileManagerError(
                f"Data filename '{filename}' must refer to a file in the data directory."
            )
        return path
