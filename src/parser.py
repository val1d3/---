"""Разбор текстового ассемблера в список словарей полей A, B, C, D."""

import re

from spec import AssemblyError, COMMANDS, check_value

REGISTER_RE = re.compile(r"R([0-9]+)", re.IGNORECASE)
NUMBER_RE = re.compile(r"(?:[0-9]+|0[xX][0-9a-fA-F]+)")


def parse_operand(token, field):
    """Читает регистр или число и проверяет диапазон поля."""
    pattern = REGISTER_RE if field.register else NUMBER_RE
    match = pattern.fullmatch(token)
    if match is None:
        kind = "регистр R0..R31" if field.register else "целое число"
        message = f"Поле {field.name}: ожидается {kind}, дано {token!r}"
        raise AssemblyError(message)
    number = match.group(1) if field.register else token
    base = 16 if number.lower().startswith("0x") else 10
    try:
        value = int(number, base)
    except ValueError as exc:
        message = f"Поле {field.name}: слишком длинное число"
        raise AssemblyError(message) from exc
    check_value(value, field.width, field.name)
    return value


def parse_instruction(line):
    """Преобразует одну непустую строку без комментария в поля команды."""
    mnemonic, *tail = line.split(maxsplit=1)
    command = COMMANDS.get(mnemonic.upper())
    if command is None:
        raise AssemblyError(f"Неизвестная команда: {mnemonic}")
    tokens = [item.strip() for item in tail[0].split(",")] if tail else []
    if len(tokens) != len(command.fields):
        raise AssemblyError(
            f"{mnemonic}: требуется аргументов {len(command.fields)}"
        )
    result = {"A": command.opcode}
    for token, field in zip(tokens, command.fields):
        result[field.name] = parse_operand(token, field)
    return result


def parse_program(text):
    """Разбирает программу; ошибки содержат номер исходной строки."""
    program = []
    for number, original in enumerate(text.splitlines(), start=1):
        line = original.split(";", 1)[0].strip()
        if not line:
            continue
        try:
            program.append(parse_instruction(line))
        except AssemblyError as exc:
            raise AssemblyError(f"Строка {number}: {exc}") from exc
    if not program:
        raise AssemblyError("Программа не содержит команд")
    return program


def format_fields(instruction):
    """Форматирует поля как A=195, B=21, C=463."""
    return ", ".join(f"{name}={value}" for name, value in instruction.items())
