"""Интерпретатор с раздельной памятью команд и данных."""

from decoder import decode_instruction
from spec import COMMAND_SIZE, COMMANDS, REGISTER_B, AssemblyError

ZERO = 0
REGISTER_COUNT = 1 << REGISTER_B.width


class ExecutionError(ValueError):
    """Ошибка выполнения программы или диапазона дампа."""


def check_range(start, end):
    """Проверяет включительный диапазон неотрицательных адресов."""
    if type(start) is not int or type(end) is not int:
        raise ExecutionError("Адреса должны быть целыми числами")
    if not ZERO <= start <= end:
        raise ExecutionError("Требуется диапазон 0 <= start <= end")


class VirtualMachine:
    """Исполняет команды; незаписанные ячейки данных содержат ноль."""

    def __init__(self, code):
        """Создаёт отдельные память команд, регистры и память данных."""
        self.code = bytes(code)
        self.registers = [ZERO] * REGISTER_COUNT
        self.memory = {}
        self.pc = ZERO
        self.operations = {
            COMMANDS["LOAD_CONST"].opcode: self.load_constant,
            COMMANDS["READ_MEM"].opcode: self.read_memory,
            COMMANDS["WRITE_MEM"].opcode: self.write_memory,
        }

    def load_constant(self, instruction):
        """Записывает константу C в регистр B."""
        self.registers[instruction["B"]] = instruction["C"]

    def read_memory(self, instruction):
        """Читает память по адресу из регистра B в регистр C."""
        address = self.registers[instruction["B"]]
        self.registers[instruction["C"]] = self.memory.get(address, ZERO)

    def write_memory(self, instruction):
        """Записывает регистр B по адресу R[D] + C."""
        address = self.registers[instruction["D"]] + instruction["C"]
        self.memory[address] = self.registers[instruction["B"]]

    def run(self):
        """Читает, декодирует и выполняет команды до конца файла."""
        if not self.code or len(self.code) % COMMAND_SIZE:
            raise ExecutionError("Нужен непустой файл из целых команд")
        while self.pc < len(self.code):
            block = self.code[self.pc:self.pc + COMMAND_SIZE]
            try:
                instruction = decode_instruction(block)
                operation = self.operations.get(instruction["A"])
                if operation is None:
                    raise ExecutionError("Операция пока не реализована")
                operation(instruction)
            except (AssemblyError, ExecutionError) as exc:
                raise ExecutionError(f"Байт {self.pc}: {exc}") from exc
            self.pc += COMMAND_SIZE

    def dump(self, start, end):
        """Возвращает адреса и значения выбранной области памяти данных."""
        check_range(start, end)
        return {
            str(address): self.memory.get(address, ZERO)
            for address in range(start, end + 1)
        }
