import machine

computer = machine.CPU()

# with open("./synacor-challenge/challenge.bin", "rb") as data:
#     program = machine.CPU.read_program_from_bin(data)
# computer.load_program(program)

# load up machine after self-tests done
computer.load_core_dump(open("./start.bin", "rb"))

# computer.debug = open("./debug.txt", "w")
computer.run()
