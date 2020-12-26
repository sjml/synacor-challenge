import sys
import os
import datetime
import pickle

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
    print("Use Ctrl-D or Ctrl-C to quit.")

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

cmd_history = []
state_stack = []
state_stack.append({
    "history": cmd_history.copy(),
    "registers": computer.registers.copy(),
    "memory": computer.mem.copy()
})
while computer.waiting_for_input:
    try:
        inp = input("> ")
    except EOFError:
        print("\nExiting!")
        break
    except KeyboardInterrupt:
        print("\nExiting!")
        break

    inp = pre_parse(inp)

    if inp:
        cmd_history.append(inp.strip())
        computer.input_buffer = inp
        computer.run()
        state_stack.append({
            "history": cmd_history.copy(),
            "registers": computer.registers.copy(),
            "memory": computer.mem.copy()
        })

if not os.path.exists("./history"):
    os.mkdir("./history")
hname = f"{datetime.datetime.now().isoformat()}.pickle"
with open(os.path.join("./history", hname), "wb") as out:
    pickle.dump(state_stack, out)
