import sys
import os

import machine

computer = machine.CPU()

# with open("./synacor-challenge/challenge.bin", "rb") as data:
#     program = machine.CPU.read_program_from_bin(data)
# computer.load_program(program)

# load up machine after self-tests done
computer.load_core_dump(open("./saves/start", "rb"))

# computer.debug = open("./debug.txt", "w")
computer.run()

shortcuts = {
    "n" : "north",
    "s" : "south",
    "e" : "east",
    "w" : "west",
    "u" : "up",
    "d" : "down",
    "i" : "inv",
    "l" : "look"
}

def save(fname):
    if not os.path.exists("./saves"):
        os.mkdir("./saves")
    fpath = os.path.join("./saves", fname)
    print(f"Saving to {fpath}...")
    with open(fpath, "wb") as save_file:
        computer.core_dump(save_file)

def load(fname):
    fpath = os.path.join("./saves", fname)
    print(f"Loading from {fpath}...")
    if not os.path.exists(fpath):
        print("ERROR: No such file.")
        return
    with open(fpath, "rb") as save_file:
        computer.load_core_dump(save_file)

def quit():
    sys.exit(0)

def pre_parse(cmd):
    parts = cmd.split(" ")

    if cmd.startswith("\\"):
        f = globals().get(parts[0][1:], None)
        if f:
            f(*parts[1:])
            return None
        else:
            print(f"ERROR: No such command '{parts[0]}'")

    if parts[0] in shortcuts.keys():
        parts[0] = shortcuts[parts[0]]

    cmd = " ".join(parts)

    if not cmd.endswith("\n"):
        cmd += "\n"
    return cmd

while computer.waiting_for_input:
    try:
        inp = input("> ")
    except EOFError:
        print("\nExiting!")
        sys.exit(0)

    inp = pre_parse(inp)

    if inp:
        computer.input_buffer = inp
        computer.run()
