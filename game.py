import sys
import os
import datetime
import pickle
import textwrap

from prompt_toolkit import Application
from prompt_toolkit.layout.containers import VSplit, HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.margins import ScrollbarMargin
from prompt_toolkit.buffer import Buffer, reshape_text
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout import Dimension, ScrollOffsets
from prompt_toolkit.widgets import Label, TextArea, Box
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

import datafiles
import machine

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

def help():
    output = [
        "All of this might break things.",
        "-------------------------------------",
        "\\save <name>: saves game to ",
        "               ./saves/<name>.bin",
        "\\load <name>: loads game from ",
        "               ./saves/<name>.bin",
        "\\mon: toggles memory monitoring",
        "\\wmem <loc> <val>: writes memory",
        "\\rmem <start> <end>: reads memory",
        "\\dreg: dumps all register values",
        "\\sreg <reg> <val>: sets a register",
        "\\warp <loc>: warps around the world",
        "\\dis <n>: disassemble the next <n>",
        "           instructions to a file",
        "           at ./disassembly.txt",
        "\\disp <n>: disassemble and pause"
        "            at the end of it",
    ]
    debug_text.buffer.text = "\n".join(output)

def save(fname):
    if not os.path.exists("./saves"):
        os.mkdir("./saves")
    fpath = os.path.join("./saves", fname)
    debug_text.buffer.text = f"Saving to {fpath}..."
    with open(fpath, "wb") as save_file:
        computer.core_dump(save_file)

def load(fname):
    fpath = os.path.join("./saves", fname)
    if not os.path.exists(fpath):
        debug_text.buffer.text = "\n".join(textwrap.wrap("ERROR: No such file.", 35))
        return
    debug_text.buffer.text = f"Loading from {fpath}..."
    with open(fpath, "rb") as save_file:
        computer.load_core_dump(save_file)

memory_monitor = False
def mon():
    global memory_monitor
    memory_monitor = not memory_monitor

def wmem(loc, val):
    if (not loc.isdigit()) or (not val.isdigit()):
        debug_text.buffer.text = "\n".join(textwrap.wrap(f"ERROR: Memory locations and values must be 15-bit uints", 35))
        return
    loc = int(loc)
    val = int(val)
    if loc < 0 or val < 0 or loc > 32676 or val > 32676:
        debug_text.buffer.text = "\n".join(textwrap.wrap(f"ERROR: Memory locations and values must be 15-bit uints.", 35))
        return
    computer.mem[loc] = val

def rmem(start, stop=None):
    if stop == None:
        stop = start
    if (not start.isdigit()) or (not stop.isdigit()):
        debug_text.buffer.text = "\n".join(textwrap.wrap(f"ERROR: Memory locations must be 15-bit uints", 35))
        return
    start = int(start)
    stop = int(stop)
    if start < 0 or stop < 0 or start > 32676 or stop > 32676:
        debug_text.buffer.text = "\n".join(textwrap.wrap(f"ERROR: Memory locations must be 15-bit uints", 35))
        return
    if stop < start:
        start, stop = stop, start
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
    if (not reg.isdigit()) or (not val.isdigit()):
        debug_text.buffer.text = "\n".join(textwrap.wrap(f"ERROR: Register indices and values must be integers", 35))
        return
    reg = int(reg)
    val = int(val)
    if reg < 0 or reg >= len(computer.registers):
        debug_text.buffer.text = "\n".join(textwrap.wrap("ERROR: Invalid register index.", 35))
        return
    if val <0 or val > 32767:
        debug_text.buffer.text = "\n".join(textwrap.wrap("ERROR: Registers hold 15-bit uints.", 35))
        return

    computer.registers[reg] = val
    dreg()

def warp(loc_idx):
    if not loc_idx.isdigit():
        debug_text.buffer.text = "\n".join(textwrap.wrap(f"ERROR: Warp locations must be integers", 35))
        return
    loc_idx = int(loc_idx)
    computer.mem[2732] = loc_idx
    computer.mem[2733] = loc_idx

# disassemble the next N instructions
def dis(count):
    if not count.isdigit():
        debug_text.buffer.text = "\n".join(textwrap.wrap(f"ERROR: Disassembly count must be integer", 35))
        return
    count = int(count)
    computer.dissassembly_count = count

# disassemble the next N instructions and then pause
def disp(count):
    if not count.isdigit():
        debug_text.buffer.text = "\n".join(textwrap.wrap(f"ERROR: Disassembly count must be integer", 35))
        return
    count = int(count)
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
            debug_text.buffer.text = "\n".join(textwrap.wrap(f"ERROR: No such command '{parts[0]}'", 35))
            return None

    if parts[0] in shortcuts.keys():
        parts[0] = shortcuts[parts[0]]

    cmd = " ".join(parts)

    if not cmd.endswith("\n"):
        cmd += "\n"
    return cmd

raw_output = ""
class UIPrinter:
    def __init__(self, target: Buffer, win: Window):
        self.target = target
        self.win = win

    def accept_output(self, val):
        global raw_output
        raw_output += chr(val)
        self.target.text += chr(val)
        self.target.cursor_position = len(self.target.text)

def diff_mem(mem1, mem2):
    diffs = []
    if len(mem1) != len(mem2):
        print(f"WARNING: Memory not the same size. ({len(mem1)} vs {len(mem2)}) Diffs will be null.")
        return diffs
    for mi in range(len(mem1)):
        if mem1[mi] == mem2[mi]:
            continue
        diffs.append((mi, mem1[mi], mem2[mi]))
    return diffs

def format_diffs(hist, idx1, idx2, regs=False, mem=True):
    out = ""
    m1 = hist[idx1]
    m2 = hist[idx2]
    reg_diffs = diff_mem(m1["registers"], m2["registers"])
    mem_diffs = diff_mem(m1["memory"], m2["memory"])
    out += f"'{m2['history'][-1]}' changes:\n"
    if regs:
        if len(reg_diffs) == 0:
            out += "\tregisters: [none]\n"
        else:
            out += "\tregisters:\n"
            for rd in reg_diffs:
                out += f"\t\t{rd[0]}: {rd[1]}\t->\t{rd[2]}\n"
    if mem:
        if len(mem_diffs) == 0:
            out += "\tmemory: [none]\n"
        else:
            out += "\tmemory:\n"
            for md in mem_diffs:
                out += f"\t\t{md[0]}: {md[1]}\t->\t{md[2]}"
                if md[2] >= 32 and md[2] < 127:
                    out += f"\t({chr(md[2])})"
                out += "\n"
    return out

def wrap_output():
    _, width = os.popen("stty size", "r").read().split()
    width = int(width) - 43
    formed = ["\n".join(textwrap.wrap(l, width)) for l in raw_output.splitlines()]
    output_buffer.text = "\n".join(formed)

def inp_handler(buff):
    global raw_output

    if not buff.text.startswith("\\"):
        raw_output += f"> {buff.text}\n\n"
        output_buffer.text += f"> {buff.text}\n\n"

    inp = pre_parse(buff.text)

    if inp:
        cmd_history.append(inp.strip())
        computer.input_buffer = inp
        computer.run()

        wrap_output()

        state_stack.append({
            "history": cmd_history.copy(),
            "registers": computer.registers.copy(),
            "memory": computer.mem.copy()
        })
        if memory_monitor:
            fdiffs = format_diffs(state_stack, -2, -1)
            debug_text.buffer.text = fdiffs
        if not computer.waiting_for_input:
            output_buffer.text += "\n\n[Game exited]\n"
            output_buffer.cursor_position = len(output_buffer.text)

output_buffer = Buffer("")
output_window = Window(
    BufferControl(buffer=output_buffer, input_processors=[]),

    wrap_lines=True,
    right_margins=[ScrollbarMargin()],
    always_hide_cursor=True,
    allow_scroll_beyond_bottom=True,
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
        Box(body=Window(content=debug_text, wrap_lines=True), width=Dimension(min=40, max=40), padding_left=1, padding_top=0, padding_bottom=0, padding_right=1),
    ],
    padding_char="‖", padding=1
)
root_layout = Layout(root)

kb = KeyBindings()

@kb.add('c-d')
def exit_(event):
    event.app.exit()

@kb.add('c-w')
def output_up_(event):
    root_layout.focus(output_buffer)
    scroll_half_page_up(event)
    root_layout.focus(input_prompt)

@kb.add('c-s')
def output_up_(event):
    root_layout.focus(output_buffer)
    scroll_half_page_down(event)
    root_layout.focus(input_prompt)


computer = machine.CPU()

# load up machine after self-tests done
computer.load_core_dump(datafiles.get("start.sav"))
computer.stdout = UIPrinter(output_buffer, output_window)

cmd_history = []
state_stack = []
state_stack.append({
    "history": cmd_history.copy(),
    "registers": computer.registers.copy(),
    "memory": computer.mem.copy()
})

computer.run()

debug_text.buffer.text = "Controls:\n\nType things and hit return.\n\Ctrl+W/S scrolls the output \nwindow.\n\nCtrl-D to quit.\n\nUse \\help to see meta commands."
wrap_output()

root_layout.focus(input_prompt)
app = Application(layout=root_layout, key_bindings=kb, full_screen=True)
app.run()

# if not os.path.exists("./history"):
#     os.mkdir("./history")
# hname = f"{datetime.datetime.now().isoformat()}.pickle"
# with open(os.path.join("./history", hname), "wb") as out:
#     pickle.dump(state_stack, out)
