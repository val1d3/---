"""Проверка машинных байтов по независимым примерам методички."""

import unittest

import test_main
from machine import encode_instruction, encode_program, format_bytes
from parser import parse_program
from spec import AssemblyError
from test_parser import EXPECTED, ROOT

EXPECTED_BYTES = (
    bytes.fromhex("C3 F5 39 00 00"),
    bytes.fromhex("F5 3C 02 00 00"),
    bytes.fromhex("52 2A 54 00 00"),
    bytes.fromhex("46 0F 24 00 00"),
)


class MachineTests(unittest.TestCase):
    """Проверки кодирования и результата второго этапа CLI."""

    def test_specification_bytes(self):
        """Каждая команда совпадает с пятью байтами из задания."""
        for instruction, expected in zip(EXPECTED, EXPECTED_BYTES):
            with self.subTest(instruction=instruction):
                self.assertEqual(encode_instruction(instruction), expected)

    def test_complete_program(self):
        """Тестовый исходник даёт 20 байт без заголовков и разделителей."""
        source = (ROOT / "examples/spec.asm").read_text(encoding="utf-8")
        code = encode_program(parse_program(source))
        self.assertEqual(code, b"".join(EXPECTED_BYTES))
        self.assertEqual(len(code), 20)

    def test_maximum_fields(self):
        """Максимальные поля не повреждают код операции и резервные биты."""
        cases = (
            ("LOAD_CONST R31, 8388607", "C3 FF FF FF 0F"),
            ("READ_MEM R31, R31", "F5 FF 03 00 00"),
            ("WRITE_MEM R31, 31, R31", "52 FF 7F 00 00"),
            ("GE R31, 31, R31", "46 FF 7F 00 00"),
        )
        for source, expected in cases:
            with self.subTest(source=source):
                code = encode_program(parse_program(source))
                self.assertEqual(code, bytes.fromhex(expected))

    def test_invalid_internal_fields(self):
        """Некорректное внутреннее представление не упаковывается."""
        cases = (
            {}, {"A": 1}, {"A": True},
            {"A": 195, "B": 0}, {"A": 195, "B": 0, "C": -1},
            {"A": 195, "B": 32, "C": 0},
            {"A": 195, "B": 0, "C": 8388608},
            {"A": 195, "B": 0, "C": 1, "D": 0},
        )
        for instruction in cases:
            with self.subTest(instruction=instruction):
                with self.assertRaises(AssemblyError):
                    encode_instruction(instruction)

    def fixture(self):
        """Создаёт файловое окружение CLI без повторного сбора его тестов."""
        fixture = test_main.MainTests()
        fixture.setUp()
        self.addCleanup(fixture.doCleanups)
        return fixture

    def test_cli_default_and_test_mode(self):
        """По умолчанию пишется бинарный файл; --test добавляет байты."""
        fixture = self.fixture()
        code, out, err = fixture.invoke("--test")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(fixture.output.read_bytes(), EXPECTED_BYTES[3])
        self.assertIn("Размер двоичного файла: 5 байт", out)
        self.assertIn(format_bytes(EXPECTED_BYTES[3]), out)
        code, out, err = fixture.invoke("--stage", "2")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(out, "Размер двоичного файла: 5 байт\n")

    def test_invalid_program_preserves_output(self):
        """Ошибка во второй строке не затирает существующий бинарный файл."""
        fixture = self.fixture()
        fixture.output.write_bytes(b"old result")
        fixture.source.write_text("GE R0, 0, R0\nBAD R0", encoding="utf-8")
        code, out, err = fixture.invoke("--stage", "2", "--test")
        self.assertEqual((code, out), (1, ""))
        self.assertIn("Строка 2", err)
        self.assertEqual(fixture.output.read_bytes(), b"old result")


if __name__ == "__main__":
    unittest.main()
