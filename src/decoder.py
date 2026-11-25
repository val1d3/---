"""Декодирование пятибайтовых команд варианта 13."""

from machine import encode_instruction
from spec import BY_OPCODE, COMMAND_SIZE, OPCODE_WIDTH, AssemblyError


def decode_instruction(block):
    """Извлекает поля команды и проверяет неиспользуемые биты."""
    if len(block) != COMMAND_SIZE:
        raise AssemblyError("Команда должна занимать пять байтов")
    word = int.from_bytes(block, byteorder="little")
    opcode = word & ((1 << OPCODE_WIDTH) - 1)
    command = BY_OPCODE.get(opcode)
    if command is None:
        raise AssemblyError(f"Неизвестный код операции: {opcode}")
    instruction = {"A": opcode}
    for field in command.fields:
        instruction[field.name] = (
            word >> field.shift
        ) & ((1 << field.width) - 1)
    if encode_instruction(instruction) != block:
        raise AssemblyError("Резервные биты команды должны быть нулевыми")
    return instruction
