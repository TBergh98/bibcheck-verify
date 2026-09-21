import json
import sqlite3
from dataclasses import asdict

from bibcheck.resolve.base import Lookup, Reference, Resolution, VerificationStatus, Work


class Cache:
    def __init__(self, path: str = "bibcheck-verify.sqlite3"):
        self.db = sqlite3.connect(path)
        self.db.execute("CREATE TABLE IF NOT EXISTS lookups (key TEXT PRIMARY KEY, payload TEXT NOT NULL)")
        self.db.commit()

    def get(self, key: str) -> Resolution | None:
        row = self.db.execute("SELECT payload FROM lookups WHERE key = ?", (key,)).fetchone()
        if not row:
            return None
        data = json.loads(row[0])
        work_data = data.get("work")
        work = Work(**work_data) if work_data else None
        lookups = []
        for item in data["lookups"]:
            matched_data = item.pop("matched", None)
            matched = Work(**matched_data) if matched_data else None
            lookups.append(Lookup(**item, matched=matched))
        return Resolution(Reference(**data["reference"]), VerificationStatus(data["status"]), data["confidence"], work, lookups, data["llm_fallback_used"])

    def put(self, key: str, resolution: Resolution) -> None:
        data = asdict(resolution)
        data["status"] = resolution.status.value
        self.db.execute("INSERT OR REPLACE INTO lookups VALUES (?, ?)", (key, json.dumps(data)))
        self.db.commit()

    def close(self) -> None:
        self.db.close()
