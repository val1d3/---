"""Проверки порядка операндов и результата команды GE."""

import unittest

from test_parser import ROOT
from test_vm import execute


class AluTests(unittest.TestCase):
    """Сравнение сохраняет целочисленный результат в исходной ячейке."""

    def test_comparison_cases(self):
        """Меньше, равно и больше дают соответственно 0, 1 и 1."""
        text = (ROOT / "examples/ge.asm").read_text(encoding="utf-8")
        machine = execute(text)
        self.assertEqual(machine.dump(100, 102), {
            "100": 0, "101": 1, "102": 1,
        })
        self.assertEqual(machine.registers[1], 185)
        self.assertTrue(all(type(value) is int for value in
                            machine.memory.values()))

    def test_maximum_offset(self):
        """GE использует смещение и не меняет соседнюю ячейку."""
        machine = execute("\n".join([
            "LOAD_CONST R31, 300", "LOAD_CONST R30, 40",
            "LOAD_CONST R29, 50", "WRITE_MEM R29, 30, R31",
            "WRITE_MEM R29, 31, R31", "GE R30, 31, R31",
        ]))
        self.assertEqual(machine.dump(330, 331), {"330": 50, "331": 1})

    def test_uninitialized_memory(self):
        """Незаписанная ячейка участвует в сравнении как ноль."""
        for threshold, expected in ((0, 1), (1, 0)):
            with self.subTest(threshold=threshold):
                machine = execute(
                    f"LOAD_CONST R1, {threshold}\nGE R1, 0, R0"
                )
                self.assertEqual(machine.dump(0, 0), {"0": expected})
