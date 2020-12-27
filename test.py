import machine

program = machine.CPU.read_program_from_bin(open("./synacor-challenge/challenge.bin", "rb"))

computer = machine.CPU()
computer.load_program(program)
computer.stdout = machine.Printer()
computer.dissassembly_count = 4096
computer.run()
