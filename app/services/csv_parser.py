"""CSV ingestion service."""
import csv
import io
from typing import Iterator


def parse_csv(content: bytes | str) -> Iterator[dict]:
    """
    Parse CSV content and yield rows as dicts.
    Handles both raw bytes (file upload) and string content.
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    reader = csv.DictReader(io.StringIO(content))
    for row in reader:
        # Strip whitespace from keys and values
        yield {k.strip(): v.strip() if v else None for k, v in row.items()}


def count_csv_rows(content: bytes | str) -> int:
    """Count rows in CSV content (excluding header)."""
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")
    reader = csv.reader(io.StringIO(content))
    next(reader, None)  # skip header
    return sum(1 for _ in reader)