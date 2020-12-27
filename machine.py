import re

MEMORY_SIZE = 32768
NUM_REGISTERS = 8

insts = [
    ## instruction name, number of arguments, dissassembler notation
    # 00
    ("halt", 0, "stop program"),
    # 01
    ("set" , 2, "set r{} to <{}>"),
    # 02
    ("push", 1, "push <{}> onto stack"),
    # 03
    ("pop" , 1, "pop stack and write to <{}>"),
    # 04
    ("eq"  , 3, "set r{} to (<{}> == <{}>)"),
    # 05
    ("gt"  , 3, "set r{} to (<{}> > <{}>)"),
    # 06
    ("jmp" , 1, "jump to <{}>"),
    # 07
    ("jt"  , 2, "if <{}>, jump to <{}>"),
    # 08
    ("jf"  , 2, "if !<{}>, jump to <{}>"),
    # 09
    ("add" , 3, "set r{} to (<{}> + <{}>)"),
    # 10
    ("mult", 3, "set r{} to (<{}> * <{}>)"),
    # 11
    ("mod" , 3, "set r{} to (<{}> % <{}>)"),
    # 12
    ("and" , 3, "set r{} to (<{}> & <{}>)"),
    # 13
    ("or"  , 3, "set r{} to (<{}> | <{}>)"),
    # 14
    ("not" , 2, "set r{} to ~<{}>"),
    # 15
    ("rmem", 2, "set r{} to mem[<{}>]"),
    # 16
    ("wmem", 2, "write <{1}> to mem[<{0}>]"),
    # 17
    ("call", 1, "call to <{}>"),
    # 18
    ("ret" , 0, "return"),
    # 19
    ("out" , 1, "output <{}>"),
    # 20
    ("int" , 1, "set r{} to input character"),
    # 21
    ("noop", 0, "no op"),
]

class Printer:
    def accept_output(self, val):
        print(chr(val), end="")

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

    def __init__(self):
        self.pc = 0
        self.mem = [0] * MEMORY_SIZE
        self.registers = [0] * NUM_REGISTERS
        self.stack = []
        self.input_buffer = ""
        self.waiting_for_input = False
        self.stdout = None
        self.debug = None
        self.ticks = -1

        self.dissassembly_count = -1
        self.disassembly_file = None

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

    disre    = re.compile(r"(<\d+>|r\d+)")
    def disassemble(self, pc):
        opcode = self.mem[pc]
        if opcode < 0 or opcode >= len(insts):
            return "---", pc+1

        inst = insts[opcode]

        if inst[1] > 0:
            raw_params = self.mem[pc+1:pc+1+inst[1]]
        else:
            raw_params = []

        output = inst[2].format(*raw_params)

        for num in CPU.disre.findall(output):
            if num.startswith("r"):
                output = output.replace(num, f"reg{int(num[1:])-32768}")
                continue
            lookup = int(num[1:-1])
            if lookup <= 32767:
                expl = str(lookup)
            else:
                lookup = lookup-32768
                val = self.registers[lookup]
                expl = f"reg{lookup} ({val})"
            output = output.replace(num, expl)

        if opcode == 15:
            # reading memory, tell value
            lookup = raw_params[1]
            if lookup < 32767:
                output += f" (value: {self.mem[lookup]})"
            else:
                reg = lookup-32768
                lookup = self.registers[reg]
                output += f" (value: {self.mem[lookup]})"
        elif opcode == 3:
            # popping stack, tell value
            output += f" (value: {self.stack[-1]})"
        elif opcode == 19:
            # printing ascii character: translate it
            if raw_params[0] < 32767:
                c = chr(raw_params[0])
            else:
                c = chr(self.registers[raw_params[0]-32768])
            output += f" ({c})"
        if opcode == 18:
                # returning, give address
                output += f" (addr: {self.stack[-1]})"

        newpc = pc + inst[1] + 1

        return output, newpc

    def read_param(self, val):
        if val < 0 or val > 32775:
            raise RuntimeError(f"Invalid param: {val}")
        if val <= 32767:
            return val
        else:
            reg = val-32768
            return self.registers[reg]

    def set_register(self, reg_idx, val):
        if reg_idx >= len(self.registers):
            reg_idx = reg_idx - 32768
        self.registers[reg_idx] = val

    def run(self):
        while True:
            if self.dissassembly_count > 0:
                self.dissassembly_count -= 1
                dis_data = self.disassemble(self.pc)
                if self.disassembly_file == None:
                    self.disassembly_file = open("./disassembly.txt", "w")
                self.disassembly_file.write(f"{self.pc}: {dis_data[0]}\n")
                self.disassembly_file.flush()
            elif self.disassembly_file != None:
                self.disassembly_file.close()
                self.disassembly_file = None

            self.ticks -= 1
            if self.ticks == 0:
                break

            opcode = self.mem[self.pc]
            if opcode >= len(insts):
                raise RuntimeError(f"Invalid opcode? {opcode} at program counter {self.pc}")
            instd = insts[opcode]
            params = [self.read_param(p) for p in self.mem[self.pc+1:self.pc+1+instd[1]]]

            if opcode == 0:
                # halt: 0
                #   stop execution and terminate the program
                break
            elif opcode == 1:
                # set: 1 a b
                #   set register <a> to the value of <b>
                self.set_register(self.mem[self.pc+1], params[1])
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
                self.set_register(self.mem[self.pc+1], self.stack.pop())
                self.pc += len(params)+1
            elif opcode == 4:
                # eq: 4 a b c
                #   set <a> to 1 if <b> is equal to <c>; set it
                #   to 0 otherwise
                self.set_register(self.mem[self.pc+1], int(params[1] == params[2]))
                self.pc += len(params)+1
            elif opcode == 5:
                # gt: 5 a b c
                #   set <a> to 1 if <b> is greater than <c>; set
                #   it to 0 otherwise
                self.set_register(self.mem[self.pc+1], int(params[1] > params[2]))
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
                val = params[1] + params[2]
                val = val & ((1<<15) - 1)
                self.set_register(self.mem[self.pc+1], val)
                self.pc += len(params)+1
            elif opcode == 10:
                # mult: 10 a b c
                #   store into <a> the product of <b> and <c>
                #   (modulo 32768)
                val = params[1] * params[2]
                val = val & ((1<<15) - 1)
                self.set_register(self.mem[self.pc+1], val)
                self.pc += len(params)+1
            elif opcode == 11:
                # mod: 11 a b c
                #   store into <a> the remainder of <b> divided
                #   by <c>
                val = params[1] % params[2]
                val = val & ((1<<15) - 1)
                self.set_register(self.mem[self.pc+1], val)
                self.pc += len(params)+1
            elif opcode == 12:
                # and: 12 a b c
                #   stores into <a> the bitwise and of <b> and <c>
                val = params[1] & params[2]
                val = val & ((1<<15) - 1)
                self.set_register(self.mem[self.pc+1], val)
                self.pc += len(params)+1
            elif opcode == 13:
                # or: 13 a b c
                #   stores into <a> the bitwise or of <b> and <c>
                val = params[1] | params[2]
                val = val & ((1<<15) - 1)
                self.set_register(self.mem[self.pc+1], val)
                self.pc += len(params)+1
            elif opcode == 14:
                # not: 14 a b
                #   stores 15-bit bitwise inverse of <b> in <a>
                val = params[1] ^ 0b111111111111111
                val = val & ((1<<15) - 1)
                self.set_register(self.mem[self.pc+1], val)
                self.pc += len(params)+1
            elif opcode == 15:
                # rmem: 15 a b
                #   read memory at address <b> and write it
                #   to <a>
                self.set_register(self.mem[self.pc+1], self.mem[params[1]])
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
                if self.stdout:
                    self.stdout.accept_output(params[0])
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
                    self.waiting_for_input = True
                    break
                self.waiting_for_input = False
                self.set_register(self.mem[self.pc+1], ord(self.input_buffer[0]))
                self.input_buffer = self.input_buffer[1:]
                self.pc += len(params)+1
            elif opcode == 21:
                # noop: 21
                #   no operation
                self.pc += 1
            else:
                raise RuntimeError(f"Invalid opcode! ({opcode} at location {self.pc})")


