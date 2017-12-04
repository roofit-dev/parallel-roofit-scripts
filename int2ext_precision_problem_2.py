import numpy as np

# for the double bounded trafo WITH DOUBLE PRECISION --> still goes wrong!


def i2e(v, u, l):
    return l + 0.5 * (u - l) * (np.sin(v) + 1)


def e2i(v, u, l, eps2):
    piby2 = 2. * np.arctan(1.)
    distnn = 8. * np.sqrt(eps2)
    vlimhi = piby2 - distnn
    vlimlo = -piby2 + distnn

    yy = 2. * (v - l) / (u - l) - 1.
    yy2 = yy * yy
    if yy2 > (1. - eps2):
        if yy < 0.:
            print("vlimlo")
            return vlimlo
        else:
            print("vlimhi")
            return vlimhi
    else:
        print("arcsin")
        return np.arcsin(yy)


def i2e2i(v_hex, u, l):
    eps2 = float.fromhex('0x1p-24')

    i = np.longdouble(float.fromhex(v_hex))
    e = np.longdouble(np.double(i2e(i, u, l)))
    i2 = e2i(e, u, l, eps2)
    return i, i2


def print_i2e2i(i, i2):
    print(i, i2)
    print(float.hex(float(i)), float.hex(float(i2)))


# -- this one happened on run 6 (7th run) of the simple 1D test WITH DOUBLE PRECISION ON!!!
right1, wrong1 = i2e2i('-0x1.ac96165639cap-3', 3, -3)
print_i2e2i(right1, wrong1)
# prints:
# (-0.20927064371719428237, -0.20927064371719426398)
# ('-0x1.ac96165639ca0p-3', '-0x1.ac96165639c9fp-3')
# i.e. the last bit is now one lower than before
# The problem is that in fact the previous solution was not properly implemented
# but instead the longdouble from i2e is first cast back to double and then
# again reinterpreted as long double for use in e2i. We need to keep everything
# long double all the time for this solution to work consistently!

# same story for run 9 (10th run):
right2, wrong2 = i2e2i('-0x1.aec2ca2d01228p-3', 3, -3)
print_i2e2i(right2, wrong2)
# (-0.21033246946184758208, -0.21033246946184759782)
# ('-0x1.aec2ca2d01228p-3', '-0x1.aec2ca2d01229p-3')
