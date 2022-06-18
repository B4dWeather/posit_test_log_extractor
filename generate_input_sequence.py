import random

from simplePositLib import *

N = 8

# a = [0.015625, 0.0625, 0.25, 0.5, 0.75, 1, 2, 3, 4, 5, 7, 10]
# b = [-12, -8, -5, -4, -3, -2, -1.5, -1, -0.5, -0.25, -0.015625]

a = 0
b = 0
c = 0
out = 0

# rappresentabili = 30
# non_rapp = 20
# with open("input_file.log", "w") as f:
#    while non_rapp > 0:
#        out = random.randint(-4, 4)
#        b = random.randint(-5, 5)
#        c = random.uniform(-1, 1)
#        a = out - (b * c)

#        if isRepresentable(a, N, 0) and isRepresentable(b, N, 0) and isRepresentable(c, N, 0):
#            if isRepresentable(out, N, 0):
#                if rappresentabili > 0:
#                    print()

# f.close()
# f.write()

binary_diff(8,'00000010', "00000010")
binary_diff(8,'00000001', "00000010")
binary_diff(8,'00000010', "00000001")
binary_diff(8,'00000101', "00000011")
binary_diff(8,'00000110', "00000011")

binary_diff(8,'00001010', "00000011")
