"""Упаковка полей варианта 13 в пятибайтовые команды little-endian."""

from spec import (
    BY_OPCODE,
    COMMAND_SIZE,
    OPCODE_WIDTH,
    AssemblyError,
    check_value,
)


def encode_instruction(instruction):
    """Проверяет поля и формирует пять байтов с нулевыми резервными битами."""
    opcode = instruction.get("A")
    check_value(opcode, OPCODE_WIDTH, "A")
    command = BY_OPCODE.get(opcode)
    if command is None:
        raise AssemblyError(f"Неизвестный код операции: {opcode}")
    expected = {"A"} | {field.name for field in command.fields}
    if set(instruction) != expected:
        raise AssemblyError("Неверный набор полей команды")
    word = opcode
    for field in command.fields:
        value = instruction[field.name]
        check_value(value, field.width, field.name)
        word |= value << field.shift
    return word.to_bytes(COMMAND_SIZE, byteorder="little")


def encode_program(program):
    """Соединяет машинные команды без заголовков и разделителей."""
    return b"".join(encode_instruction(instruction) for instruction in program)


def format_bytes(block):
    """Форматирует байты как 0xC3, 0xF5, 0x39, 0x00, 0x00."""
    return ", ".join(f"0x{value:02X}" for value in block)
