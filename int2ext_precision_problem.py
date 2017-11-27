import numpy as np

# for the double bounded trafo


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

    i = float.fromhex(v_hex)
    e = i2e(i, u, l)
    i2 = e2i(e, u, l, eps2)
    return i, i2


def print_i2e2i(i, i2):
    print(i, i2)
    print(float.hex(i), float.hex(i2))


# this is the first number in my test that goes wrong
right1, wrong1 = i2e2i('-0x1.abadef0339ab8p-3', 3, -3)
print_i2e2i(right1, wrong1)
# prints:
# -0.20882784584610703 -0.208827845846
# -0x1.abadef0339ab8p-3 -0x1.abadef0339ab9p-3
# i.e. the last bit is now one higher than before
# let's try another:
print_i2e2i(*i2e2i('-0x1.abadef0339ab9p-3', 3, -3))
# that goes fine...
# another:
print_i2e2i(*i2e2i('-0x1.abadef0339abap-3', 3, -3))
# aha, this also goes wrong, with same result!
print_i2e2i(*i2e2i('-0x1.abadef0339abbp-3', 3, -3))
# also!
print_i2e2i(*i2e2i('-0x1.abadef0339ab7p-3', 3, -3))
# also! still same value!
print_i2e2i(*i2e2i('-0x1.abadef0339ab6p-3', 3, -3))
# still wrong, now different value.
print_i2e2i(*i2e2i('-0x1.abadef0339ab5p-3', 3, -3))
# that is a correct one again.
# So basically in this range ~1/3 of results are wrong...
