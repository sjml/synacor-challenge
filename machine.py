MEMORY_SIZE = 32768
NUM_REGISTERS = 8

insts = [
    ("halt", 0),  # 00
    ("set" , 2),  # 01
    ("push", 1),  # 02
    ("pop" , 1),  # 03
    ("eq"  , 3),  # 04
    ("gt"  , 3),  # 05
    ("jmp" , 1),  # 06
    ("jt"  , 2),  # 07
    ("jf"  , 2),  # 08
    ("add" , 3),  # 09
    ("mult", 3),  # 10
    ("mod" , 3),  # 11
    ("and" , 3),  # 12
    ("or"  , 3),  # 13
    ("not" , 2),  # 14
    ("rmem", 2),  # 15
    ("wmem", 2),  # 16
    ("call", 1),  # 17
    ("ret" , 0),  # 18
    ("out" , 1),  # 19
    ("int" , 1),  # 20
    ("noop", 0),  # 21
]

class CPU:
    @staticmethod
    def read_program_from_bin(data_file):
        program = []
        while True:
            b = data_file.read(2)
            if len(b) < 2:
                break
            val = (b[1] << 8) + b[0]
            if val > 32776 or val < 0:
                raise RuntimeError(f"Invalid program bytes @ position {data_file.tell()-2}: {b[0]:0X} {b[0]:0X}")
            program.append(val)
        return program

    def __init__(self, run_self_test=False):
        self.pc = 0
        self.mem = [0] * MEMORY_SIZE
        self.registers = [0] * NUM_REGISTERS
        self.stack = []
        self.input_buffer = ""
        self.debug = None

    def load_program(self, program):
        self.mem = [0] * MEMORY_SIZE
        for i, b in enumerate(program):
            self.mem[i] = b

    def core_dump(self, output_file):
        if output_file == None:
            out = open("./dump.bin", "wb")
        else:
            out = output_file
        def encode(n) -> bytes:
            return bytes([n & 0x00FF, n >> 8])
        out.write(encode(self.pc))
        out.write(encode(len(self.stack))) # assumption: stack can't grow beyond int limit
        for s in self.stack:
            out.write(encode(s))
        for r in self.registers:
            out.write(encode(r))
        for m in self.mem:
            out.write(encode(m))
        if output_file == None:
            out.close()

    def load_core_dump(self, dump_file):
        self.pc = 0
        self.mem = [0] * MEMORY_SIZE
        self.registers = [0] * NUM_REGISTERS
        self.stack = []

        def get_next():
            b = dump_file.read(2)
            if len(b) < 2:
                raise RuntimeError(f"Core dump corruption.")
            val = (b[1] << 8) + b[0]
            if val > 32776 or val < 0:
                raise RuntimeError(f"Invalid program bytes @ position {dump_file.tell()-2}: {b[0]:0X} {b[0]:0X}")
            return val

        self.pc = get_next()
        stack_len = get_next()
        for _ in range(stack_len):
            self.stack.append(get_next())
        for ri in range(NUM_REGISTERS):
            self.registers[ri] = get_next()
        for m in range(MEMORY_SIZE):
            self.mem[m] = get_next()


    def read_param(self, val):
        if val < 0 or val > 32775:
            raise RuntimeError(f"Invalid param: {val}")
        if val <= 32767:
            return val
        else:
            return self.registers[val-32768]

    def run(self):
        while True:
            opcode = self.mem[self.pc]
            instd = insts[opcode]
            params = [self.read_param(p) for p in self.mem[self.pc+1:self.pc+1+instd[1]]]

            if self.debug:
                self.debug.write(f"{instd[0]}: {self.mem[self.pc+1:self.pc+1+instd[1]]} (pc:{self.pc})\n")
                self.debug.write(f"\tparams: {params}\n")
                self.debug.write(f"\tregisters: {self.registers}\n")
                self.debug.write(f"\tstack len: {len(self.stack)}\n")
                self.debug.flush()

            if opcode == 0:
                # halt: 0
                #   stop execution and terminate the program
                break
            elif opcode == 1:
                # set: 1 a b
                #   set register <a> to the value of <b>
                reg = self.mem[self.pc+1] - 32768
                self.registers[reg] = params[1]
                self.pc += len(params)+1
            elif opcode == 2:
                # push: 2 a
                #   push <a> onto the stack
                self.stack.append(params[0])
                self.pc += len(params)+1
            elif opcode == 3:
                # pop: 3 a
                #   remove the top element from the stack and
                #   write it into <a>; empty stack = error
                reg = self.mem[self.pc+1] - 32768
                self.registers[reg] = self.stack.pop()
                self.pc += len(params)+1
            elif opcode == 4:
                # eq: 4 a b c
                #   set <a> to 1 if <b> is equal to <c>; set it
                #   to 0 otherwise
                reg = self.mem[self.pc+1] - 32768
                if params[1] == params[2]:
                    self.registers[reg] = 1
                else:
                    self.registers[reg] = 0
                self.pc += len(params)+1
            elif opcode == 5:
                # gt: 5 a b c
                #   set <a> to 1 if <b> is greater than <c>; set
                #   it to 0 otherwise
                reg = self.mem[self.pc+1] - 32768
                if params[1] > params[2]:
                    self.registers[reg] = 1
                else:
                    self.registers[reg] = 0
                self.pc += len(params)+1
            elif opcode == 6:
                # jmp: 6 a
                #   jump to <a>
                self.pc = params[0]
            elif opcode == 7:
                # jt: 7 a b
                #   if <a> is nonzero, jump to <b>
                if params[0] != 0:
                    self.pc = params[1]
                else:
                    self.pc += len(params)+1
            elif opcode == 8:
                # jf: 8 a b
                #   if <a> is zero, jump to <b>
                if params[0] == 0:
                    self.pc = params[1]
                else:
                    self.pc += len(params)+1
            elif opcode == 9:
                # add: 9 a b c
                #   assign into <a> the sum of <b> and <c> (modulo
                #   32768)
                reg = self.mem[self.pc+1] - 32768
                val = params[1] + params[2]
                val = val & ((1<<15) - 1)
                self.registers[reg] = val
                self.pc += len(params)+1
            elif opcode == 10:
                # mult: 10 a b c
                #   store into <a> the product of <b> and <c>
                #   (modulo 32768)
                reg = self.mem[self.pc+1] - 32768
                val = params[1] * params[2]
                val = val & ((1<<15) - 1)
                self.registers[reg] = val
                self.pc += len(params)+1
            elif opcode == 11:
                # mod: 11 a b c
                #   store into <a> the remainder of <b> divided
                #   by <c>
                reg = self.mem[self.pc+1] - 32768
                val = params[1] % params[2]
                val = val & ((1<<15) - 1)
                self.registers[reg] = val
                self.pc += len(params)+1
            elif opcode == 12:
                # and: 12 a b c
                #   stores into <a> the bitwise and of <b> and <c>
                reg = self.mem[self.pc+1] - 32768
                val = params[1] & params[2]
                val = val & ((1<<15) - 1)
                self.registers[reg] = val
                self.pc += len(params)+1
            elif opcode == 13:
                # or: 13 a b c
                #   stores into <a> the bitwise or of <b> and <c>
                reg = self.mem[self.pc+1] - 32768
                val = params[1] | params[2]
                val = val & ((1<<15) - 1)
                self.registers[reg] = val
                self.pc += len(params)+1
            elif opcode == 14:
                # not: 14 a b
                #   stores 15-bit bitwise inverse of <b> in <a>
                reg = self.mem[self.pc+1] - 32768
                val = params[1] ^ 0b111111111111111
                val = val & ((1<<15) - 1)
                self.registers[reg] = val
                self.pc += len(params)+1
            elif opcode == 15:
                # rmem: 15 a b
                #   read memory at address <b> and write it
                #   to <a>
                reg = self.mem[self.pc+1] - 32768
                self.registers[reg] = self.mem[params[1]]
                self.pc += len(params)+1
            elif opcode == 16:
                # wmem: 16 a b
                #   write the value from <b> into memory at
                #   address <a>
                self.mem[params[0]] = params[1]
                self.pc += len(params)+1
            elif opcode == 17:
                # call: 17 a
                #   write the address of the next instruction to
                #   the stack and jump to <a>
                self.stack.append(self.pc+len(params)+1)
                self.pc = params[0]
            elif opcode == 18:
                # ret: 18
                #   remove the top element from the stack and jump
                #   to it; empty stack = halt
                if len(self.stack) == 0:
                    break
                self.pc = self.stack.pop()
            elif opcode == 19:
                # out: 19 a
                #   write the character represented by ascii code
                #   <a> to the terminal
                print(chr(params[0]), end="")
                self.pc += len(params)+1
            elif opcode == 20:
                # in: 20 a
                #   read a character from the terminal and write
                #   its ascii code to <a>; it can be assumed that
                #   once input starts, it will continue until a
                #   newline is encountered; this means that you can
                #   safely read whole lines from the keyboard and
                #   trust that they will be fully read
                if len(self.input_buffer) == 0:
                    self.input_buffer = input("> ")
                    self.input_buffer += "\n"
                reg = self.mem[self.pc+1] - 32768
                self.registers[reg] = ord(self.input_buffer[0])
                self.input_buffer = self.input_buffer[1:]
                self.pc += len(params)+1
            elif opcode == 21:
                # noop: 21
                #   no operation
                self.pc += 1
            else:
                raise RuntimeError(f"Invalid opcode! {opcode}")


