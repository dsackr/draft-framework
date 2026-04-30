from __future__ import annotations

import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from unittest import mock

from draft_table.cli import build_parser, find_available_port


class CliTests(unittest.TestCase):
    def test_cli_defines_required_commands(self) -> None:
        parser = build_parser()

        for command in ("onboard", "serve", "validate", "chat", "ai", "repo", "commit", "doctor"):
            with self.subTest(command=command):
                with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                    with self.assertRaises(SystemExit) as context:
                        parser.parse_args([command, "--help"])
                self.assertEqual(context.exception.code, 0)

    def test_cli_rejects_one_shot_ask_command(self) -> None:
        parser = build_parser()

        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            with self.assertRaises(SystemExit) as context:
                parser.parse_args(["ask", "What is an ABB?"])

        self.assertNotEqual(context.exception.code, 0)

    def test_find_available_port_returns_port_number(self) -> None:
        fake_socket = mock.MagicMock()
        fake_socket.__enter__.return_value.getsockname.return_value = ("127.0.0.1", 5000)
        with mock.patch("socket.socket", return_value=fake_socket):
            port = find_available_port()

        self.assertEqual(port, 5000)


if __name__ == "__main__":
    unittest.main()
