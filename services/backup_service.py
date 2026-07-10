from __future__ import annotations

import base64
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from config.app_config import AppConfig
from services.mysql_source import MySqlSource


class BackupService:
    def __init__(self, config: AppConfig, db_path: Path | None = None) -> None:
        self.config = config
        self.db_path = Path(db_path or MySqlSource().sqlite_path)
        self.backup_dir = self.config.project_root / "backups"
        self.iterations = 390000

    def create_backup(self, *, password: str = "", tag: str = "manual") -> Path:
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        payload = self._dump_database(tag)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if password:
            path = self.backup_dir / f"prm_billing_inventory_{tag}_{stamp}.pgst"
            path.write_text(json.dumps(self._encrypt_payload(payload, password), indent=2), encoding="utf-8")
            self._log("backup-encrypted", path, "Success", "Encrypted desktop backup created.")
            return path
        path = self.backup_dir / f"prm_billing_inventory_{tag}_{stamp}.json"
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")
        self._log("backup", path, "Success", "Desktop JSON backup created.")
        return path

    def restore_backup(self, path: Path, *, password: str = "") -> Path:
        backup_path = Path(path)
        payload = self._read_payload(backup_path, password)
        pre_restore = self.create_backup(tag="pre_restore")
        self._restore_payload(payload)
        self._log("restore", backup_path, "Success", f"Restored. Safety backup: {pre_restore}")
        return pre_restore

    def _dump_database(self, tag: str) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            tables = self._tables(conn)
            data: dict[str, list[dict[str, Any]]] = {}
            for table in tables:
                rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
                data[table] = [dict(row) for row in rows]
        return {
            "format": "PRM_BILLING_INVENTORY_BACKUP",
            "version": 1,
            "tag": tag,
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "database": self.db_path.name,
            "tables": data,
        }

    def _read_payload(self, path: Path, password: str) -> dict[str, Any]:
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("format") == "PRM_BILLING_INVENTORY_PGST":
            if not password:
                raise ValueError("Password is required for encrypted backup files.")
            raw = self._decrypt_payload(raw, password)
        if raw.get("format") != "PRM_BILLING_INVENTORY_BACKUP":
            raise ValueError("This file is not a PRM Billing Inventory backup.")
        if not isinstance(raw.get("tables"), dict):
            raise ValueError("Backup file does not contain table data.")
        return raw

    def _restore_payload(self, payload: dict[str, Any]) -> None:
        tables = payload["tables"]
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            existing = set(self._tables(conn))
            restore_tables = [table for table in tables.keys() if table in existing]
            with conn:
                for table in reversed(restore_tables):
                    conn.execute(f'DELETE FROM "{table}"')
                for table in restore_tables:
                    rows = tables.get(table) or []
                    if not rows:
                        continue
                    columns = list(rows[0].keys())
                    quoted = ", ".join(f'"{column}"' for column in columns)
                    placeholders = ", ".join("?" for _ in columns)
                    sql = f'INSERT INTO "{table}" ({quoted}) VALUES ({placeholders})'
                    conn.executemany(sql, [[row.get(column) for column in columns] for row in rows])

    def _tables(self, conn: sqlite3.Connection) -> list[str]:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
        return [str(row[0]) for row in rows]

    def _encrypt_payload(self, payload: dict[str, Any], password: str) -> dict[str, Any]:
        salt = os.urandom(16)
        iv = os.urandom(16)
        key = self._key(password, salt)
        source = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
        padder = padding.PKCS7(128).padder()
        padded = padder.update(source) + padder.finalize()
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        encryptor = cipher.encryptor()
        encrypted = encryptor.update(padded) + encryptor.finalize()
        return {
            "format": "PRM_BILLING_INVENTORY_PGST",
            "cipher": "AES-256-CBC",
            "kdf": "PBKDF2-SHA256",
            "iterations": self.iterations,
            "salt": base64.b64encode(salt).decode("ascii"),
            "iv": base64.b64encode(iv).decode("ascii"),
            "payload": base64.b64encode(encrypted).decode("ascii"),
        }

    def _decrypt_payload(self, envelope: dict[str, Any], password: str) -> dict[str, Any]:
        salt = base64.b64decode(envelope["salt"])
        iv = base64.b64decode(envelope["iv"])
        encrypted = base64.b64decode(envelope["payload"])
        key = self._key(password, salt, int(envelope.get("iterations") or self.iterations))
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
        decryptor = cipher.decryptor()
        padded = decryptor.update(encrypted) + decryptor.finalize()
        unpadder = padding.PKCS7(128).unpadder()
        source = unpadder.update(padded) + unpadder.finalize()
        return json.loads(source.decode("utf-8"))

    def _key(self, password: str, salt: bytes, iterations: int | None = None) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=iterations or self.iterations,
        )
        return kdf.derive(password.encode("utf-8"))

    def _log(self, action: str, path: Path, status: str, message: str) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO backup_logs(action,file_path,status,message,created_at) VALUES(?,?,?,?,?)",
                    (action, str(path), status, message, datetime.now().isoformat(timespec="seconds")),
                )
                conn.commit()
        except sqlite3.Error:
            return
