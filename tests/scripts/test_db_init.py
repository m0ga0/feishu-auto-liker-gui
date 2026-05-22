"""Tests for database initialization script"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from parkbot.scripts.db_init import init_database


class TestDBInit:
    """Test database initialization"""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        # Cleanup
        if os.path.exists(path):
            os.remove(path)

    def test_init_database_creates_tables(self, temp_db_path, capsys):
        """Test that init_database creates tables successfully"""
        with patch("parkbot.scripts.db_init.DB_PATH", temp_db_path):
            with patch("parkbot.scripts.db_init.MonitorSettingsDB") as mock_db:
                mock_metadata = MagicMock()
                mock_db.metadata = mock_metadata

                init_database()

                # Verify create_all was called
                mock_metadata.create_all.assert_called_once()

                # Verify success message was printed
                captured = capsys.readouterr()
                assert "Database initialized" in captured.out
                assert temp_db_path in captured.out

    def test_init_database_with_real_engine(self, temp_db_path, capsys):
        """Integration test with real SQLAlchemy engine"""
        with patch("parkbot.scripts.db_init.DB_PATH", temp_db_path):
            init_database()

            # Verify database file was created
            assert os.path.exists(temp_db_path)
            assert os.path.getsize(temp_db_path) > 0

            # Verify success message
            captured = capsys.readouterr()
            assert "Database initialized" in captured.out

    def test_init_database_multiple_calls_idempotent(self, temp_db_path):
        """Test that calling init_database multiple times is safe"""
        with patch("parkbot.scripts.db_init.DB_PATH", temp_db_path):
            # First call
            init_database()
            assert os.path.exists(temp_db_path)

            # Second call should not fail
            init_database()
            assert os.path.exists(temp_db_path)

    def test_init_database_invalid_path(self):
        """Test error handling for invalid database path"""
        with patch("parkbot.scripts.db_init.DB_PATH", "/nonexistent/path/db.sqlite"):
            with pytest.raises(Exception):
                init_database()

    def test_main_block_execution(self):
        """Test that the __main__ block calls init_database"""
        with patch("parkbot.scripts.db_init.init_database") as mock_init:
            # Simulate running as __main__
            import parkbot.scripts.db_init as db_init_module

            db_init_module.init_database()
            mock_init.assert_called_once()
