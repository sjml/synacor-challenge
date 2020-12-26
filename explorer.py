import sys
import os
import pickle

if not os.path.exists("./history"):
    print("ERROR: No history files to explore!")
    sys.exit(1)

histories = [f for f in os.listdir("./history") if f.endswith(".pickle")]
histories.sort()

latest = histories[-1]

hist = pickle.load(open(os.path.join("./history", latest), "rb"))

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

for mi, moment in enumerate(hist):
    if mi == 0:
        continue
    reg_diffs = diff_mem(hist[mi-1]["registers"], moment["registers"])
    mem_diffs = diff_mem(hist[mi-1]["memory"], moment["memory"])
    print(f"'{moment['history'][-1]}' changes:")
    if len(reg_diffs) == 0:
        print("\tregisters: [none]")
    else:
        print("\tregisters:")
        for rd in reg_diffs:
            print(f"\t\t{rd[0]}: {rd[1]}\t->\t{rd[2]}")
    if len(mem_diffs) == 0:
        print("\tmemory: [none]")
    else:
        print("\tmemory:")
        for md in mem_diffs:
            print(f"\t\t{md[0]}: {md[1]}\t->\t{md[2]}")
