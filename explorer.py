import sys
import os
import pickle

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


if __name__ == "__main__":
    if not os.path.exists("./history"):
        print("ERROR: No history files to explore!")
        sys.exit(1)

    histories = [f for f in os.listdir("./history") if f.endswith(".pickle")]
    histories.sort()

    latest = histories[-1]

    hist = pickle.load(open(os.path.join("./history", latest), "rb"))

    for mi in range(len(hist)):
        if mi == 0:
            continue
        print(format_diffs(hist, mi-1, mi))
