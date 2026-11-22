"""Проверки языка ассемблера и примеров спецификации варианта 13."""

import unittest
from pathlib import Path

from parser import format_fields, parse_program
from spec import AssemblyError

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = [
    {"A": 195, "B": 21, "C": 463},
    {"A": 245, "B": 28, "C": 17},
    {"A": 82, "B": 10, "C": 1, "D": 21},
    {"A": 70, "B": 15, "C": 0, "D": 9},
]


class ParserTests(unittest.TestCase):
    """Поля, диапазоны, синтаксис и диагностика исходной программы."""

    def test_specification(self):
        """Файл примера даёт все четыре набора полей из методички."""
        source = (ROOT / "examples/spec.asm").read_text(encoding="utf-8")
        self.assertEqual(parse_program(source), EXPECTED)
        self.assertEqual(format_fields(EXPECTED[0]), "A=195, B=21, C=463")

    def test_comments_case_and_hex(self):
        """Разрешены комментарии, табуляция, разный регистр и hex-числа."""
        source = "; начало\n\nload_const\tr21, 0x1CF ; конец\n"
        self.assertEqual(parse_program(source), [EXPECTED[0]])

    def test_boundaries(self):
        """Минимумы и максимумы всех видов операндов допустимы."""
        source = "\n".join([
            "LOAD_CONST R0, 0", "LOAD_CONST R31, 8388607",
            "READ_MEM R0, R31", "WRITE_MEM R31, 31, R0",
            "GE R0, 0, R31",
        ])
        self.assertEqual(len(parse_program(source)), 5)

    def test_invalid_programs(self):
        """Неизвестные команды, неверные типы и диапазоны отклоняются."""
        cases = (
            "", "; только комментарий", "UNKNOWN R1", "READ_MEM R1",
            "READ_MEM R1, R2, R3", "READ_MEM R1 R2", "READ_MEM R1,",
            "READ_MEM 1, R2", "READ_MEM R1, R32", "READ_MEM R-1, R0",
            "LOAD_CONST R32, 0", "LOAD_CONST R0, -1",
            "LOAD_CONST R0, 8388608", "LOAD_CONST R0, 1.5",
            "LOAD_CONST R0, 0x", "LOAD_CONST R0, R1",
            "WRITE_MEM R0, 32, R1", "WRITE_MEM R0, 0, R32",
        )
        for source in cases:
            with self.subTest(source=source):
                with self.assertRaises(AssemblyError):
                    parse_program(source)

    def test_line_number(self):
        """Номер ошибки учитывает пустые строки и комментарии."""
        with self.assertRaisesRegex(AssemblyError, "Строка 3"):
            parse_program("; комментарий\n\nREAD_MEM R0, R32")


if __name__ == "__main__":
    unittest.main()
