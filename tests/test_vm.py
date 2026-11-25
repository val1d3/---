"""Проверки декодера, раздельной памяти и копирования массива."""

import unittest

from decoder import decode_instruction
from machine import encode_program
from parser import parse_program
from spec import COMMAND_SIZE, AssemblyError
from test_parser import EXPECTED, ROOT
from vm import ExecutionError, VirtualMachine


def execute(text):
    """Собирает текстовую программу и возвращает выполненную УВМ."""
    machine = VirtualMachine(encode_program(parse_program(text)))
    machine.run()
    return machine


class DecoderTests(unittest.TestCase):
    """Декодер проверяется на независимых байтах спецификации."""

    def test_specification(self):
        """Все четыре команды восстанавливают заданные поля."""
        blocks = (
            "C3 F5 39 00 00", "F5 3C 02 00 00",
            "52 2A 54 00 00", "46 0F 24 00 00",
        )
        for block, expected in zip(blocks, EXPECTED):
            with self.subTest(block=block):
                self.assertEqual(
                    decode_instruction(bytes.fromhex(block)), expected,
                )

    def test_invalid_commands(self):
        """Отклоняются обрыв, лишние байты, неизвестный код и резерв."""
        blocks = (b"", b"\xc3" * 4, b"\xc3" * 6, bytes(5))
        reserved = bytes.fromhex("C3 F5 39 00 80")
        for block in (*blocks, reserved):
            with self.subTest(block=block):
                with self.assertRaises(AssemblyError):
                    decode_instruction(block)


class VirtualMachineTests(unittest.TestCase):
    """Операции с регистрами и данными не изменяют память команд."""

    def test_copy_array(self):
        """Три элемента копируются, а исходный массив сохраняется."""
        text = (ROOT / "examples/copy.asm").read_text(encoding="utf-8")
        machine = execute(text)
        self.assertEqual(machine.dump(100, 102), {
            "100": 10, "101": 20, "102": 30,
        })
        self.assertEqual(machine.dump(200, 202), {
            "200": 10, "201": 20, "202": 30,
        })
        self.assertEqual(machine.pc, 16 * COMMAND_SIZE)

    def test_separate_memory(self):
        """Запись по адресу ноль не повреждает первую машинную команду."""
        text = "LOAD_CONST R31, 8388607\nWRITE_MEM R31, 0, R0"
        machine = execute(text)
        self.assertEqual(machine.memory[0], 8388607)
        self.assertEqual(machine.code, encode_program(parse_program(text)))

    def test_zero_initialization_and_dump(self):
        """Регистры и незаписанные ячейки изначально содержат ноль."""
        machine = execute("READ_MEM R0, R31")
        self.assertEqual(machine.registers, [0] * 32)
        self.assertEqual(machine.dump(4, 5), {"4": 0, "5": 0})
        self.assertEqual(machine.dump(5, 5), {"5": 0})

    def test_invalid_binary(self):
        """Пустая, оборванная и повреждённая программы не выполняются."""
        for code in (b"", b"\xc3", bytes(5)):
            with self.subTest(code=code):
                with self.assertRaises(ExecutionError):
                    VirtualMachine(code).run()

    def test_registers_and_offset(self):
        """Адрес, значение и максимальное смещение не перепутаны."""
        machine = execute("\n".join([
            "LOAD_CONST R31, 500", "LOAD_CONST R30, 42",
            "WRITE_MEM R30, 31, R31", "LOAD_CONST R29, 531",
            "READ_MEM R29, R28",
        ]))
        self.assertEqual(machine.registers[28], 42)
        self.assertEqual(machine.dump(530, 531), {"530": 0, "531": 42})

    def test_invalid_dump_range(self):
        """Отрицательные, перевёрнутые и нецелые границы отклоняются."""
        machine = execute("LOAD_CONST R0, 0")
        for start, end in ((-1, 2), (2, 1), (True, 2), (0, 1.5)):
            with self.subTest(start=start, end=end):
                with self.assertRaises(ExecutionError):
                    machine.dump(start, end)
