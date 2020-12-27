import sys
import os
import datetime
import pickle
import textwrap

from prompt_toolkit import Application
from prompt_toolkit.layout.containers import VSplit, HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.margins import ScrollbarMargin
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout import Dimension, ScrollOffsets
from prompt_toolkit.widgets import Label, TextArea
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.processors import TabsProcessor
from prompt_toolkit.key_binding.bindings.scroll import (
    scroll_backward,
    scroll_forward,
    scroll_half_page_down,
    scroll_half_page_up,
    scroll_one_line_down,
    scroll_one_line_up,
    scroll_page_down,
    scroll_page_up,
)

import machine
from explorer import diff_mem, format_diffs

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
    # print(f"Saving to {fpath}...")
    with open(fpath, "wb") as save_file:
        computer.core_dump(save_file)

def load(fname):
    fpath = os.path.join("./saves", fname)
    # print(f"Loading from {fpath}...")
    if not os.path.exists(fpath):
        # print("ERROR: No such file.")
        return
    with open(fpath, "rb") as save_file:
        computer.load_core_dump(save_file)

def wmem(loc, val):
    loc = int(loc)
    val = int(val)
    # print("ERROR: Memory locations and values must be integers.")
    computer.mem[loc] = val

def rmem(start, stop=None):
    if stop == None:
        stop = start
    start = int(start)
    stop = int(stop)
    # print("ERROR: Memory locations and values must be integers.")
    if stop < start:
        start, stop = stop, start
        # print("ERROR: stop < start")
    out = ""
    while start <= stop:
        out += f"{start}: {computer.mem[start]}\n"
        start += 1
    debug_text.buffer.text = out

def dreg():
    out = "registers:\n"
    for i, r in enumerate(computer.registers):
        out += f"\t{i}:\t{r}\n"
    debug_text.buffer.text = out

def sreg(reg, val):
    reg = int(reg)
    val = int(val)
    # print("ERROR: Register indices and values must be integers.")
    if reg < 0 or reg >= len(computer.registers):
        # print("ERROR: Invalid register index.")
        return
    computer.registers[reg] = val
    dreg()

def warp(loc_idx):
    loc_idx = int(loc_idx)
    # print("ERROR: Memory locations and values must be integers.")
    computer.mem[2732] = loc_idx
    computer.mem[2733] = loc_idx

def rep(count, *commands):
    count = int(count)
    cmd_str = " ".join(commands)
    cmds = cmd_str.split(" | ")
    out = "\n".join(cmds) + "\n"
    out *= count
    return out

# disassemble the next N instructions
def dis(count):
    count = int(count)
    # print("ERROR: Disassembly count must be integer.")
    computer.dissassembly_count = count

# disassemble the next N instructions and then pause
def disp(count):
    count = int(count)
    # print("ERROR: Disassembly count must be integer.")
    computer.dissassembly_count = count
    computer.ticks = count

def pre_parse(cmd):
    parts = cmd.split(" ")

    if cmd.startswith("\\"):
        f = globals().get(parts[0][1:], None)
        if f:
            f(*parts[1:])
            return None
        else:
            debug_text.buffer.text = f"ERROR: No such command '{parts[0]}'"
            return None

    if parts[0] in shortcuts.keys():
        parts[0] = shortcuts[parts[0]]

    cmd = " ".join(parts)

    if not cmd.endswith("\n"):
        cmd += "\n"
    return cmd

class UIPrinter:
    def __init__(self, target):
        self.target = target

    def accept_output(self, val):
        self.target.text += chr(val)
        self.target.cursor_position = len(self.target.text)

def inp_handler(buff):
    output_buffer.text += f"> {buff.text}\n\n"

    inp = pre_parse(buff.text)

    if inp:
        cmd_history.append(inp.strip())
        computer.input_buffer = inp
        computer.run()
        state_stack.append({
            "history": cmd_history.copy(),
            "registers": computer.registers.copy(),
            "memory": computer.mem.copy()
        })
        fdiffs = format_diffs(state_stack, -2, -1)
        debug_text.buffer.text = fdiffs
        if not computer.waiting_for_input:
            output_buffer.text += "\n\n[Game exited]\n"
            output_buffer.cursor_position = len(output_buffer.text)

output_buffer = Buffer("")
output_window = Window(
    BufferControl(buffer=output_buffer),

    wrap_lines=True,
    right_margins=[ScrollbarMargin()],
    always_hide_cursor=True,
    allow_scroll_beyond_bottom=True
)

prompt_history = InMemoryHistory()
input_prompt = TextArea("", multiline=False, height=Dimension(max=1), history=prompt_history, accept_handler=inp_handler, prompt="> ")

debug_text = BufferControl(Buffer(""), input_processors=[TabsProcessor(char1=" ", char2=" ")])

root = VSplit(
    [
        HSplit(
            [
                output_window,
                input_prompt
            ],
            padding_char="-", padding=1,

        ),
        Window(content=debug_text, width=Dimension(min=40, max=40)),
    ],
    padding_char="‖", padding=1
)
root_layout = Layout(root)

kb = KeyBindings()

@kb.add('c-d')
def exit_(event):
    event.app.exit()

@kb.add('s-up')
def output_up_(event):
    root_layout.focus(output_buffer)
    scroll_half_page_up(event)
    root_layout.focus(input_prompt)

@kb.add('s-down')
def output_up_(event):
    root_layout.focus(output_buffer)
    scroll_half_page_down(event)
    root_layout.focus(input_prompt)


computer = machine.CPU()

# load up machine after self-tests done
computer.load_core_dump(open("./saves/start", "rb"))
computer.stdout = UIPrinter(output_buffer)

cmd_history = []
state_stack = []
state_stack.append({
    "history": cmd_history.copy(),
    "registers": computer.registers.copy(),
    "memory": computer.mem.copy()
})

computer.run()

root_layout.focus(input_prompt)
app = Application(layout=root_layout, key_bindings=kb, full_screen=True)
app.run()

# if not os.path.exists("./history"):
#     os.mkdir("./history")
# hname = f"{datetime.datetime.now().isoformat()}.pickle"
# with open(os.path.join("./history", hname), "wb") as out:
#     pickle.dump(state_stack, out)
