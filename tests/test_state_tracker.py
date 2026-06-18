import sys
import os
import tempfile
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.state_tracker import StateTracker

class TestStateTracker:
    def setup_method(self):
        # Create a temporary file for the database path
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        self.tracker = StateTracker(self.db_path)

        # Create a temporary file to track
        self.temp_file_fd, self.temp_file_path = tempfile.mkstemp(suffix=".json")
        with open(self.temp_file_path, "w") as f:
            f.write('{"data": [1, 2, 3]}')

    def teardown_method(self):
        # Clean up files
        os.close(self.db_fd)
        os.close(self.temp_file_fd)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)

    def test_init_db(self):
        # Verify db file is created and has the schema
        assert os.path.exists(self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='processed_files'")
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "processed_files"

    def test_tracking_lifecycle(self):
        stage = "test_stage"
        # 1. Unprocessed file should return False
        assert not self.tracker.is_processed(stage, self.temp_file_path)

        # 2. Mark processed and verify it returns True
        self.tracker.mark_processed(stage, self.temp_file_path)
        assert self.tracker.is_processed(stage, self.temp_file_path)

        # 3. If file changes content, it should return False
        with open(self.temp_file_path, "w") as f:
            f.write('{"data": [1, 2, 3, 4]}')
        assert not self.tracker.is_processed(stage, self.temp_file_path)

        # 4. Non-existent file should return False
        assert not self.tracker.is_processed(stage, "/non/existent/path")
