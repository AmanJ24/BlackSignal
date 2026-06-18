import sqlite3
import os
import hashlib
import logging

logger = logging.getLogger("StateTracker")

class StateTracker:
    def __init__(self, db_path: str):
        self.db_path = str(db_path)
        self._init_db()

    def _init_db(self):
        try:
            db_dir = os.path.dirname(self.db_path)
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS processed_files (
                        stage_name TEXT,
                        file_path TEXT,
                        file_hash TEXT,
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (stage_name, file_path)
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"❌ Failed to initialize state database at {self.db_path}: {e}")

    def is_processed(self, stage_name: str, file_path: str) -> bool:
        """
        Checks if a file has already been processed by a specific stage
        by comparing its base name and SHA256 checksum.
        """
        if not os.path.exists(file_path):
            return False

        try:
            file_hash = self._get_file_hash(file_path)
            basename = os.path.basename(file_path)
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT file_hash FROM processed_files WHERE stage_name = ? AND file_path = ?",
                    (stage_name, basename)
                )
                row = cursor.fetchone()
                if row and row[0] == file_hash:
                    return True
        except Exception as e:
            logger.error(f"⚠️ State check error for {file_path} in stage {stage_name}: {e}")
        return False

    def mark_processed(self, stage_name: str, file_path: str):
        """
        Saves the file path, stage, and SHA256 checksum to mark it as processed.
        """
        if not os.path.exists(file_path):
            return

        try:
            file_hash = self._get_file_hash(file_path)
            basename = os.path.basename(file_path)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO processed_files (stage_name, file_path, file_hash) VALUES (?, ?, ?)",
                    (stage_name, basename, file_hash)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"⚠️ Failed to mark file {file_path} as processed for stage {stage_name}: {e}")

    def _get_file_hash(self, file_path: str) -> str:
        hasher = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(65536), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
