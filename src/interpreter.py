"""CLI интерпретатора УВМ с сохранением дампа данных в JSON."""

import argparse
import json
import sys
from pathlib import Path

from main import EXIT_ERROR, EXIT_OK, validate_paths
from spec import COMMAND_SIZE, AssemblyError
from vm import ExecutionError, VirtualMachine, check_range


def parse_args(argv):
    """Читает бинарный файл, путь дампа и включительный диапазон."""
    parser = argparse.ArgumentParser(description="Интерпретатор, вариант 13")
    parser.add_argument("-i", "--input", required=True, help="входной .bin")
    parser.add_argument("-o", "--output", required=True, help="дамп JSON")
    parser.add_argument(
        "--start", type=int, required=True, help="первый адрес",
    )
    parser.add_argument(
        "--end", type=int, required=True, help="последний адрес",
    )
    return parser.parse_args(argv)


def run(args):
    """Исполняет программу и сохраняет дамп после успешного выполнения."""
    source, output = Path(args.input), Path(args.output)
    validate_paths(source, output)
    check_range(args.start, args.end)
    machine = VirtualMachine(source.read_bytes())
    machine.run()
    result = json.dumps(machine.dump(args.start, args.end), indent=2)
    output.write_text(result + "\n", encoding="utf-8")
    print(f"Выполнено команд: {machine.pc // COMMAND_SIZE}")
    print(f"Дамп памяти: {output}")


def main(argv=None):
    """Возвращает код завершения и выводит понятное сообщение об ошибке."""
    args = parse_args(argv)
    try:
        run(args)
    except (AssemblyError, ExecutionError, OSError, UnicodeError) as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return EXIT_ERROR
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
