"""Проверки интерфейса интерпретатора и сохранности входных файлов."""

import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import interpreter
from machine import encode_program
from parser import parse_program
from test_parser import ROOT


class InterpreterTests(unittest.TestCase):
    """CLI сохраняет JSON только после успешного выполнения программы."""

    def setUp(self):
        """Создаёт изолированные входной файл и путь результата."""
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.source = Path(directory.name) / "program.bin"
        self.output = Path(directory.name) / "dump.json"
        text = (ROOT / "examples/copy.asm").read_text(encoding="utf-8")
        self.source.write_bytes(encode_program(parse_program(text)))

    def invoke(self, *extra):
        """Запускает CLI с перехватом стандартных потоков."""
        arguments = [
            "-i", str(self.source), "-o", str(self.output),
            "--start", "200", "--end", "202", *extra,
        ]
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            result = interpreter.main(arguments)
        return result, out.getvalue(), err.getvalue()

    def test_json_dump(self):
        """CLI сохраняет адреса и скопированные значения в JSON."""
        result, out, err = self.invoke()
        self.assertEqual((result, err), (0, ""))
        self.assertIn("Выполнено команд: 16", out)
        self.assertEqual(
            json.loads(self.output.read_text(encoding="utf-8")),
            {"200": 10, "201": 20, "202": 30},
        )

    def test_same_path(self):
        """Дамп нельзя записать поверх бинарной программы."""
        original = self.source.read_bytes()
        result, out, err = self.invoke("-o", str(self.source))
        self.assertEqual((result, out), (1, ""))
        self.assertIn("должны различаться", err)
        self.assertEqual(self.source.read_bytes(), original)

    def test_invalid_binary_preserves_dump(self):
        """Ошибка поздней команды не затирает предыдущий дамп."""
        self.output.write_text("old dump", encoding="utf-8")
        self.source.write_bytes(self.source.read_bytes() + bytes(5))
        result, out, err = self.invoke()
        self.assertEqual((result, out), (1, ""))
        self.assertIn("Байт 80", err)
        self.assertEqual(self.output.read_text(encoding="utf-8"), "old dump")

    def test_invalid_range(self):
        """Недопустимый диапазон не создаёт выходного файла."""
        result, out, err = self.invoke("--start", "203")
        self.assertEqual((result, out), (1, ""))
        self.assertIn("диапазон", err)
        self.assertFalse(self.output.exists())

    def test_missing_input(self):
        """Отсутствующий бинарный файл даёт понятную ошибку."""
        self.source.unlink()
        result, out, err = self.invoke()
        self.assertEqual((result, out), (1, ""))
        self.assertIn("не найден", err)
