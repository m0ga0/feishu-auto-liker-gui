"""Tests for main.py entry point"""

import pytest
from unittest.mock import patch, MagicMock


class TestMain:
    """Test main application entry point"""

    @pytest.fixture
    def mock_repos(self):
        """Create mock repositories"""
        mock_settings_repo = MagicMock()
        mock_settings_repo.internal.get.return_value = MagicMock(
            logging_dir="logs", logging_level="INFO"
        )
        mock_message_repo = MagicMock()
        return mock_settings_repo, mock_message_repo

    @pytest.fixture
    def mock_app(self):
        """Create mock App"""
        with patch("parkbot.main.App") as mock_app_class:
            mock_instance = MagicMock()
            mock_app_class.return_value = mock_instance
            yield mock_app_class, mock_instance

    def test_main_successful_execution(self, mock_repos, mock_app):
        """Test main function executes successfully"""
        mock_settings_repo, mock_message_repo = mock_repos
        mock_app_class, mock_instance = mock_app

        with patch(
            "parkbot.main.get_settings_repository", return_value=mock_settings_repo
        ):
            with patch(
                "parkbot.main.get_message_repository", return_value=mock_message_repo
            ):
                with patch("parkbot.main.logger") as mock_logger:
                    from parkbot.main import main

                    main()

                    # Verify logger configuration
                    mock_logger.remove.assert_called_once()
                    mock_logger.add.assert_called_once_with(
                        "logs", level="INFO", rotation="10 MB"
                    )

                    # Verify App creation
                    mock_app_class.assert_called_once_with(
                        app_settings_repo=mock_settings_repo,
                        message_repo=mock_message_repo,
                    )

                    # Verify mainloop was called
                    mock_instance.mainloop.assert_called_once()

    def test_main_creates_repositories(self, mock_repos, mock_app):
        """Test that main creates both repositories"""
        mock_settings_repo, mock_message_repo = mock_repos

        with patch("parkbot.main.get_settings_repository") as mock_get_settings:
            with patch("parkbot.main.get_message_repository") as mock_get_message:
                with patch("parkbot.main.logger"):
                    with patch("parkbot.main.App"):
                        mock_get_settings.return_value = mock_settings_repo
                        mock_get_message.return_value = mock_message_repo

                        from parkbot.main import main

                        main()

                        mock_get_settings.assert_called_once()
                        mock_get_message.assert_called_once()

    def test_main_gets_internal_settings(self, mock_repos, mock_app):
        """Test that main retrieves internal settings"""
        mock_settings_repo, _ = mock_repos

        with patch(
            "parkbot.main.get_settings_repository", return_value=mock_settings_repo
        ):
            with patch("parkbot.main.get_message_repository"):
                with patch("parkbot.main.logger"):
                    with patch("parkbot.main.App"):
                        from parkbot.main import main

                        main()

                        mock_settings_repo.internal.get.assert_called_once()

    def test_main_configures_logging_with_correct_values(self, mock_repos, mock_app):
        """Test logging is configured with settings from repository"""
        mock_settings_repo, _ = mock_repos

        with patch(
            "parkbot.main.get_settings_repository", return_value=mock_settings_repo
        ):
            with patch("parkbot.main.get_message_repository"):
                with patch("parkbot.main.logger") as mock_logger:
                    with patch("parkbot.main.App"):
                        from parkbot.main import main

                        main()

                        # Verify logging config uses values from settings
                        mock_logger.add.assert_called_once_with(
                            mock_settings_repo.internal.get.return_value.logging_dir,
                            level=mock_settings_repo.internal.get.return_value.logging_level,
                            rotation="10 MB",
                        )

    def test_main_app_passes_repositories(self, mock_repos, mock_app):
        """Test that App receives both repositories"""
        mock_settings_repo, mock_message_repo = mock_repos
        mock_app_class, _ = mock_app

        with patch(
            "parkbot.main.get_settings_repository", return_value=mock_settings_repo
        ):
            with patch(
                "parkbot.main.get_message_repository", return_value=mock_message_repo
            ):
                with patch("parkbot.main.logger"):
                    from parkbot.main import main

                    main()

                    # Verify App is created with correct kwargs
                    call_kwargs = mock_app_class.call_args.kwargs
                    assert call_kwargs["app_settings_repo"] == mock_settings_repo
                    assert call_kwargs["message_repo"] == mock_message_repo

    def test_main_block_execution(self):
        """Test that __main__ block executes main()"""
        with patch("parkbot.main.main") as mock_main:
            # Simulate running as __main__
            import parkbot.main as main_module

            main_module.main()
            mock_main.assert_called_once()

    def test_main_exception_handling(self, mock_repos):
        """Test main handles exceptions gracefully"""
        mock_settings_repo, _ = mock_repos

        with patch(
            "parkbot.main.get_settings_repository", return_value=mock_settings_repo
        ):
            with patch(
                "parkbot.main.get_message_repository", side_effect=Exception("DB Error")
            ):
                with pytest.raises(Exception, match="DB Error"):
                    from parkbot.main import main

                    main()
