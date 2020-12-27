import re

import machine

START = 5454 # program counter after we've checked that
             #  highest register is not equal to 0

computer = machine.CPU()
computer.load_core_dump(open("./saves/hq", "rb"))


disre = re.compile(r"(<\d*>|r\d*)")


for addr in range(5454,5466):
    print(f"{addr}: {disassemble(addr)[0]}")
    break
