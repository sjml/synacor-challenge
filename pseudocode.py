# import sys
# sys.setrecursionlimit(10000)

# # load hq
# # patch: 5483: set reg0 to 4
#     # change 5485 to 0
# # patch: 5491: set reg1 to (reg0 (2) == 6)
#     # change 5494 to 2
# # set register 7 to 1
# # disp 16384
# # use teleporter

# 5483: set reg0 to 4
# 5486: set reg1 to 1
# patch:
#   \wmem 5485 0
#   \wmem 5488 5
# \sreg 7 25734
# \disp 16384
# use teleporter

r0 = 4
r1 = 1
r2 = 3 # ???
r3 = 10 # ???
r4 = 101 # ???
r5 = 0 # ???
r6 = 0 # ???
r7 = 1 # [my value]
stack = []

# def dump():
#     out = ""
#     out += f" r0: {r0}, "
#     out += f" r1: {r1}, "
#     out += f" r7: {r7}, "
#     # out += f"{str(stack)}\n"
#     print(out)

def _6027():
    global r0, r1, r2, r3, r4, r5, r6, r7
    if r0 != 0: # 6027
        # jumped to 6305
        if r1 != 0: # 6035
            # jumped to 6048
            stack.append(r0) # 6048
            r1 = (r1 + 32767) % 32768 # 6050
            _6027() # 6054
            r1 = r0 # 6056
            r0 = stack.pop() # 6059
            r0 = (r0 + 32767) % 32768 # 6061
            _6027() # 6065
            return # 6067
        r0 = (r0 + 32767) % 32768 # 6038
        r1 = r7 # 6042
        _6027() # 6045
        return # 6047

    r0 = (r1 + 1) % 32768 # 6030
    return # 6034

# def _1531():
#     print("Miscalibration.")

# def _1458():
#     global r0, r1, r2, r3, r4, r5, r6, r7
#     stack.append(r0) # 1458
#     stack.append(r3) # 1460
#     stack.append(r4) # 1462
#     stack.append(r5) # 1464
#     stack.append(r6) # 1466
#     r6 = r0 # 1468
#     r5 = r1 # 1471
#     r4 = 144 # 1474 (memory read from @reg0: 29400)
#     r1 = 0 # 1477
#     r3 = 1 + r1 # 1480
#     r0 = int(r3 > r4) # 1484
#     if r0 != 0: # 1488
#         # jump to 1507
#         reg6 = stack.pop() # 1507
#         reg5 = stack.pop() # 1509
#         reg4 = stack.pop() # 1511
#         reg3 = stack.pop() # 1513
#         reg0 = stack.pop() # 1515
#         return # 1517
#     r3 = (r3 + r6) % 32768 # 1491
#     r0 = 29749 # 1495 (memory read from @reg3: 29401)
#     _1531() # 1498


# _6027() # 5489

# r1 = r0 # 5491 (r0 is 2 if we patched)
# if r1 == 0: # 5495
#     # jumped to 5579
#     stack.append(r0) # 5579
#     stack.append(r1) # 5581
#     stack.append(r2) # 5583
#     r0 = 29400
#     r1 = 1531
#     r2 = 1933 + 27879
#     _1458()



from functools import cache
import sys
sys.setrecursionlimit(10**9)
import threading
threading.stack_size(134213632) # 128-ish megabytes

@cache
def f1(a,b,magic):
    if a == 0:
        return (b + 1) % 32768
    if b == 0:
        return f1(a-1, magic, magic)
    return f1(a-1, f1(a, b-1, magic), magic)

def main():
    # try all the numbers in 15-bit int range to see
    #   which one gives me the correct answer of 6
    start = 1
    end = 32768
    for i in range(start, end):

        answer = f1(4,1,i)

        # forgot to do this initially and watched it gobble
        #  all my RAM and ~15 gigs of swap in about a minute
        f1.cache_clear()

        # unnecessary, but stdout is not the bottleneck here
        print(i, answer)

        if answer == 6:
            break

main_thread = threading.Thread(target=main)
main_thread.start()
main_thread.join()

# 25734
