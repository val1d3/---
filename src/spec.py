"""Поля команд учебной виртуальной машины, вариант 13."""

from dataclasses import dataclass

COMMAND_SIZE = 5
MIN_VALUE = 0
OPCODE_WIDTH = 8


class AssemblyError(ValueError):
    """Ошибка исходной программы или промежуточного представления."""


@dataclass(frozen=True)
class Field:
    """Имя, положение, ширина и вид операнда."""

    name: str
    shift: int
    width: int
    register: bool


@dataclass(frozen=True)
class Command:
    """Код операции и поля в порядке аргументов ассемблера."""

    opcode: int
    fields: tuple


REGISTER_B = Field("B", 8, 5, True)
REGISTER_C = Field("C", 13, 5, True)
REGISTER_D = Field("D", 18, 5, True)
CONSTANT_C = Field("C", 13, 23, False)
OFFSET_C = Field("C", 13, 5, False)

COMMANDS = {
    "LOAD_CONST": Command(195, (REGISTER_B, CONSTANT_C)),
    "READ_MEM": Command(245, (REGISTER_B, REGISTER_C)),
    "WRITE_MEM": Command(82, (REGISTER_B, OFFSET_C, REGISTER_D)),
    "GE": Command(70, (REGISTER_B, OFFSET_C, REGISTER_D)),
}
BY_OPCODE = {command.opcode: command for command in COMMANDS.values()}


def check_value(value, width, name):
    """Проверяет целое беззнаковое значение заданной битовой ширины."""
    maximum = (1 << width) - 1
    if type(value) is not int or not MIN_VALUE <= value <= maximum:
        raise AssemblyError(f"Поле {name}: нужно целое от 0 до {maximum}")
