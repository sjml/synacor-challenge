import itertools
vals = {2: "red", 3: "corroded", 5: "shiny", 7: "concave", 9: "blue"}

for order in itertools.permutations(vals.keys()):
    total = order[0] + order[1] * (order[2] ** 2) + (order[3] ** 3) - order[4]
    if total == 399:
        for k in order:
            print(vals[k])
        break

# red coin (2 dots)
# corroded coin (triangle)
# shiny coin (pentagon)
# concave coin (7 dots)
# blue coin (9 dots)

# _ + _ * _^2 + _^3 - _ = 399


## Answer:
# blue
# red
# shiny
# concave
# corroded
