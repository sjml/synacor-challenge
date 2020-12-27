class Op:
    def __init__(self, desc):
        opstr = desc[0]
        if opstr == "+":
            self.op = 0
        elif opstr == "-":
            self.op = 1
        elif opstr == "*":
            self.op = 2
        self.val = int(desc[1:])
        self.desc = desc

    def __repr__(self):
        return self.desc

    def apply_to(self, num):
        if self.op == 0:
            num += self.val
        elif self.op == 1:
            num -= self.val
        elif self.op == 2:
            num *= self.val
        return num


web = {
    (0,3): [
        (Op("-9"), (2,3)), (Op("-4"), (1,2)), (Op("+4"), (1,2)), (Op("+4"), (0,1))
    ],
    (0,1): [
        (Op("+4"), (1,2)), (Op("*4"), (1,2)), (Op("*11"), (2,1)), (Op("*8"), (1,0))
    ],
    (1,2): [
        (Op("-9"), (2,3)), (Op("-18"), (3,2)), (Op("-11"), (2,1)), (Op("*11"), (2,1)),
        (Op("*4"), (0,1)), (Op("+4"), (0,1))
    ],
    (1,0): [
        (Op("*4"), (0,1)), (Op("*11"), (2,1)), (Op("-11"), (2,1)), (Op("-1"), (3,0))
    ],
    (2,3): [
        (Op("-4"), (1,2)), (Op("-18"), (3,2)), (Op("*18"), (3,2))
    ],
    (2,1): [
        (Op("-1"), (3,0)), (Op("-8"), (1,0)), (Op("*1"), (3,0)), (Op("*18"), (3,2)),
        (Op("-18"), (3,2)), (Op("-4"), (1,2)), (Op("*8"), (1,0)), (Op("*4"), (1,2))
    ],
    (3,2): [
        (Op("*1"), (3,0)), (Op("*11"), (2,1)), (Op("-11"), (2,1)), (Op("-9"), (2,3)),
        (Op("*9"), (2,3))
    ]
}

import heapq

def pathfind(start, end):
    frontier = []
    heapq.heappush(frontier, (0, start))
    source_map = {}
    path_cost = {}
    source_map[start] = None
    path_cost[start] = 0

    while len(frontier) > 0:
        current = heapq.heappop(frontier)[1]
        if current == end:
            break
        xy = (current[0], current[1])
        w = current[2]
        for n in web[xy]:
            px,py = n[1]
            pw = n[0].apply_to(w)
            if pw < 0 or pw > 32767:
                continue # orb weight can't overflow
            if px == goalX and py == goalY and pw != goalW:
                continue # can't enter goal at wrong weight
            node = (px, py, pw)
            cost = path_cost[current]
            if node not in path_cost or cost < path_cost[node]:
                path_cost[node] = cost + 1
                priority = cost
                heapq.heappush(frontier, (priority, node))
                source_map[node] = current

    if end not in source_map:
        return False, []

    found_path = []
    while current != start:
        found_path.append(current)
        current = source_map[current]
    found_path.append(start)
    found_path.reverse()

    return True, found_path

goalX = 3
goalY = 0
startX = 0
startY = 3

startW = 22
goalW = 30

goal =  ( goalX,  goalY,  goalW) # to be at weight 30 when at x=3 and y=0
start = (startX, startY, startW) # start at weight 22 at x=0 and y=3


_, path = pathfind(start, goal)
print(path)
print(len(path))

# shorter!
# [(0, 3, 22), (1, 2, 26), (2, 1, 15), (1, 2, 60), (3, 2, 42), (2, 1, 31), (3, 0, 30)]
# manual mapping:
#            n e         e n         w s         e e         w n         n e

# north east east north west south east east west north north east



# [(0, 3, 22), (0, 1, 26), (1, 2, 30), (0, 1, 34), (1, 2, 38), (2, 3, 29), (1, 2, 25), (0, 1, 29), (1, 2, 33), (0, 1, 37), (1, 2, 41), (2, 1, 30), (3, 0, 30)]
# manual mapping:
#            n n         s e         w n         s e         e s         w n         w n         s e         w n         s e         e n         e n

# north
# north
# south
# east
# west
# north
# south
# east
# east
# south
# west
# north
# west
# north
# south
# east
# west
# north
# south
# east
# east
# north
# east
# north
