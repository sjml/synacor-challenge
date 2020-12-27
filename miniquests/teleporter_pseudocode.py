# was taking notes of pseudocode as I examined the assembly,
# eventually turned into Python to run it and play some more


r0 = 4
r1 = 1
r7 = 1 # [magic number]
stack = []

def _6027():
    global r0, r1, r7
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

