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

# using the threading stuff seems to be the only (easy?) way
#  to increase the stack size :-/
main_thread = threading.Thread(target=main)
main_thread.start()
main_thread.join()

# magic number is: 25734

# \wmem 5485 0  # set r0 to short-circuit value
# \wmem 5488 5  # set r1 to short-circuit value
# \sreg 7 25734 # set r7 to magic number
# \disp 16384 # (optional, only if you wanna see the assembly as it's run)
# use teleporter
