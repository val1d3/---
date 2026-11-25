"""Три программы этапа 5 проверяются по явным ожидаемым результатам."""

import unittest

from machine import encode_program
from parser import parse_program
from test_parser import ROOT
from vm import VirtualMachine


class VectorTests(unittest.TestCase):
    """Все шесть результатов записываются в адреса исходного вектора."""

    def check_vector(self, name, expected):
        """Собирает пример, выполняет его и проверяет весь массив."""
        source = ROOT / "examples" / f"{name}.asm"
        code = encode_program(parse_program(source.read_text("utf-8")))
        self.assertEqual(len(code), 100)
        machine = VirtualMachine(code)
        machine.run()
        self.assertEqual(machine.memory, {
            address: value
            for address, value in enumerate(expected, start=100)
        })
        self.assertEqual(machine.pc, len(code))

    def test_mixed(self):
        """Проверяются ноль, граница 185 и максимальная константа."""
        self.check_vector("vector_mixed", [0, 0, 1, 1, 1, 1])

    def test_below(self):
        """Все значения ниже 185 превращаются в нули."""
        self.check_vector("vector_below", [0, 0, 0, 0, 0, 0])

    def test_above(self):
        """Значения от 185 включительно превращаются в единицы."""
        self.check_vector("vector_above", [1, 1, 1, 1, 1, 1])
