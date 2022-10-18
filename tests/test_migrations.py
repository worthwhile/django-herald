from django.core.management import call_command
from django.test import TestCase

from mock import patch


class MigrationTests(TestCase):
    def test_no_migrations_created(self):
        with patch("sys.exit") as exit_mocked:
            call_command(
                "makemigrations", "herald", dry_run=True, check=True, verbosity=0
            )
            exit_mocked.assert_not_called()
