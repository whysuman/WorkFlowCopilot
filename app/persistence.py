import json
from typing import Dict, Any

def append_jsonl(path: str, record: Dict[str, Any]) -> None:
    """Append a single JSON record to a JSONL file."""
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

