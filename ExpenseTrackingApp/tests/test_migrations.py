"""Integration and regression tests for PostgreSQL migrations."""

from __future__ import annotations

import re
import shutil
import subprocess
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory


REPO_ROOT = Path(__file__).resolve().parent.parent
MIGRATION_001 = REPO_ROOT / "migrations" / "001_create_transactions.sql"
MIGRATION_002 = REPO_ROOT / "migrations" / "002_reject_nan_amounts.sql"
IMPORT_SCRIPT = REPO_ROOT / "data_curation" / "import_transactions.sql"


class MigrationSourceTests(unittest.TestCase):
    def test_historical_staging_explicitly_rejects_nan(self) -> None:
        source = IMPORT_SCRIPT.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            re.compile(
                r"CONSTRAINT\s+historical_transactions_import_amount_check"
                r"\s+CHECK\s*\("
                r"amount\s*>\s*0\s+AND\s+"
                r"amount\s*<>\s*'NaN'::numeric"
                r"\s*\)",
                re.IGNORECASE,
            ),
        )


class RejectNanMigrationIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        required_commands = ("initdb", "pg_ctl", "psql")
        cls.commands = {
            command: shutil.which(command) for command in required_commands
        }
        missing = [
            command for command, path in cls.commands.items() if path is None
        ]
        if missing:
            raise unittest.SkipTest(
                "PostgreSQL integration tools not available: "
                + ", ".join(missing)
            )

        cls.temp_dir = TemporaryDirectory()
        cls.temp_path = Path(cls.temp_dir.name)
        cls.data_dir = cls.temp_path / "data"
        cls.socket_dir = cls.temp_path / "socket"
        cls.socket_dir.mkdir()

        initialized = subprocess.run(
            [
                cls.commands["initdb"],
                "--auth=trust",
                "--no-locale",
                "--encoding=UTF8",
                "--username=postgres",
                f"--pgdata={cls.data_dir}",
            ],
            capture_output=True,
            text=True,
        )
        if initialized.returncode != 0:
            raise RuntimeError(
                "initdb failed for the temporary test cluster:\n"
                + initialized.stderr
            )
        subprocess.run(
            [
                cls.commands["pg_ctl"],
                f"--pgdata={cls.data_dir}",
                "--wait",
                "--log",
                str(cls.temp_path / "postgres.log"),
                "--options",
                (
                    f"-F -k {cls.socket_dir} "
                    "-c listen_addresses='' "
                    "-c unix_socket_permissions=0700"
                ),
                "start",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        if hasattr(cls, "data_dir"):
            subprocess.run(
                [
                    cls.commands["pg_ctl"],
                    f"--pgdata={cls.data_dir}",
                    "--wait",
                    "stop",
                ],
                check=False,
                capture_output=True,
                text=True,
            )
        if hasattr(cls, "temp_dir"):
            cls.temp_dir.cleanup()

    def psql(
        self,
        *,
        command: str | None = None,
        file: Path | None = None,
        tuples_only: bool = False,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        arguments = [
            self.commands["psql"],
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "--host",
            str(self.socket_dir),
            "--username",
            "postgres",
            "--dbname",
            "postgres",
        ]
        if tuples_only:
            arguments.extend(["--tuples-only", "--no-align"])
        if command is not None:
            arguments.extend(["--command", command])
        if file is not None:
            arguments.extend(["--file", str(file)])
        return subprocess.run(
            arguments,
            check=check,
            capture_output=True,
            text=True,
            cwd=REPO_ROOT,
        )

    def insert_amount(self, amount: str) -> subprocess.CompletedProcess[str]:
        return self.psql(
            command=(
                "INSERT INTO public.transactions "
                "(occurred_on, transaction_type, amount, description) "
                f"VALUES (DATE '2026-07-28', 'expense', {amount}, "
                "'Amount constraint test');"
            ),
            check=False,
        )

    def test_migration_repairs_nan_and_enforces_amount_domain(self) -> None:
        self.psql(file=MIGRATION_001)
        inserted = self.psql(
            command=(
                "INSERT INTO public.transactions "
                "(occurred_on, transaction_type, amount, description, updated_at) "
                "VALUES (DATE '2026-07-28', 'expense', 'NaN'::numeric, "
                "'Legacy NaN', TIMESTAMPTZ '2000-01-01 00:00:00+00') "
                "RETURNING id;"
            ),
            tuples_only=True,
        )
        repaired_id = inserted.stdout.strip().splitlines()[0]

        migrated = self.psql(file=MIGRATION_002)
        self.assertRegex(
            migrated.stdout,
            rf"(?m)^\s*{re.escape(repaired_id)}\s*$",
        )

        repaired = self.psql(
            command=(
                "SELECT amount::text || '|' || updated_at::text "
                "FROM public.transactions "
                f"WHERE id = {repaired_id};"
            ),
            tuples_only=True,
        ).stdout.strip()
        repaired_amount, repaired_updated_at = repaired.split("|", maxsplit=1)
        self.assertEqual(repaired_amount, "0.01")
        self.assertNotEqual(repaired_updated_at, "2000-01-01 00:00:00+00")

        for invalid_amount in (
            "'NaN'::numeric",
            "0",
            "-0.01",
            "10000000000.00",
        ):
            with self.subTest(invalid_amount=invalid_amount):
                result = self.insert_amount(invalid_amount)
                self.assertNotEqual(result.returncode, 0)

        for valid_amount in ("12.34", "9999999999.99"):
            with self.subTest(valid_amount=valid_amount):
                result = self.insert_amount(valid_amount)
                self.assertEqual(result.returncode, 0, result.stderr)

        snapshot_query = (
            "SELECT id::text || '|' || amount::text || '|' || updated_at::text "
            "FROM public.transactions ORDER BY id;"
        )
        before_rerun = self.psql(
            command=snapshot_query,
            tuples_only=True,
        ).stdout
        self.psql(file=MIGRATION_002)
        after_rerun = self.psql(
            command=snapshot_query,
            tuples_only=True,
        ).stdout
        self.assertEqual(after_rerun, before_rerun)


if __name__ == "__main__":
    unittest.main()
