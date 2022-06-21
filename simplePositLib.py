# ---------------------------------------------------------------
from os import listdir

# ---------------------------------------------------------------
# Simple python library for some posit operations
# ---------------------------------------------------------------
# Usage Example:
#   # put your posit (which you have in HEX) in a variable
#   in_hex = some posit number, represented as HEX on N/4 digits
#   # you can convert it in binary
#   pp_bin = hex2bit(in_hex, N)
#   # you can convert it in real
#   pp_real = posit2real(pp_bin,N,ES) #ES is the number of exponent bits
# ---------------------------------------------------------------
# List of functions:
#
#   >> a2comp(bits, expected_len=8):
#       compute 2's complement of a bit string
#
#   >> sign(n)
#       compute the sign of a function. oddly, this function is not available by default in python (it's in numpy)
#
#   >> get_regime(posit_bits, size):
#       extract the regime of a bit string representing a posit, of a given size
#
#   >> bit2fraction(bits):
#       calculate the fractional part of a posit
#
#   >> posit2real(bits, p_size=8, es_size=0):
#       convert a string of bits representing a Posit number in a real number
#       TODO: this feature is not implemented yet for exponents different than 0
#
#   >> hex2bit(hex_in, expected_len):
#       convert a string representing a hexadecimal number in a binary number, having a given expected length
#
# function:
#   >> real2posit(real: float, p_size, es_size):
#       convert a real number in a string of bit representing a posit
#       TODO: this is just a quick attempt left unfinished; it is not working correctly
#
#   >> isRepresentable(num, p_size, es_size):
#       check if a number is posit_representable.
#       TODO: this feature rely on lookup tables, saved in files for given formats.
#           if the real2posit function is ever finished, it can replace the use of lookup tables
#
#   >> binary_sum(max_size, b1, b2):
#       calculate additions between binary numbers. operands and result are encoded as strings
#
#   >> binary_diff(max_size, b1, b2):
#       calculate subtractions between binary numbers. operands and result are encoded as strings
#
# ---------------------------------------------------------------
# ---------------------------------------------------------------
# ------------------- config parameters: ------------------------
table_folder = "table"  # folder containing posit lookup tables

# cache_max_size -1 is unlimited; cache_max_size 0 is to remove this feature
cache_max_size = -1
# ------------------ internal variables: ------------------------
# in order to avoid closing and opening the file several times, the numbers read in there are saved in a local array
representable_numbers_cache = []


# ---------------------------------------------------------------
# ---------------- function implementation: ---------------------
# function: compute the A2 complement of a bit string
def a2comp(bits, expected_len=8):
    # $ parameters $
    # $bits: a steam of (0,1), representing bits to be complemented
    # $expected_len: number of bits of the output; zero padding is applied if necessary
    complement = ""
    i = 0
    reduced = bin(int(bits, 2) - 1)[2:].zfill(expected_len)
    for bit in reduced:
        if bit == '0':
            complement += '1'
        else:
            complement += '0'
        i += 1
    converted = bin(int(complement, 2))
    # returns the A2 complement represented on the desired number of bits
    return converted[2:].zfill(expected_len)


# function: compute the sign of a function
# oddly, looks like this function require numpy, and it's not default included in python
def sign(n):
    # $ parameters $
    # $ n: real number
    # returns 1 for positive numbers and -1 for negative numbers
    if n > 0:
        return 1
    else:
        return -1


# function: compute the regime of the given Posit
def get_regime(posit_bits, size):
    # $ parameters $
    # $posit_bits: posit number encoded as a binary string
    # $size: the number of bits in posit_bits
    m = 0
    i = 1
    if posit_bits[1] == '0':
        while posit_bits[i] == '0':
            m -= 1
            i += 1
            if i >= size:
                break
    if posit_bits[1] == '1':
        while posit_bits[i] == '1':
            m += 1
            i += 1
            if i >= size:
                break
        m -= 1
    # returns regime and regime length as numbers
    return m, i


# function: calculate the fractional part of a posit
def bit2fraction(bits):
    # $ parameters $
    # $bits: the terminal bits of a posit number, representing the fractional part
    f = 1
    i = 1
    for bit in bits:
        if bit == '1':
            f += pow(2, -1 * i)
        i += 1
    # returns the fractional part as a number, which lays in [1,2]
    return f


# function: convert a string of bits representing a Posit number in a real number
def posit2real(bits, p_size=8, es_size=0):
    # $ parameters $
    # $bits: a string of bits representing a posit
    # $p_size: the number of bits on which the number $bits is represented
    # $es_size: the number of bits reserved for the posit exponent
    # check zero beforehand
    if all(c in '0' for c in bits):
        return 0
    s = 1
    if bits[0] == '1':
        s = -1
    if s < 0:
        bits = a2comp(bits, p_size)
    k, regime_size = get_regime(bits, p_size)
    if es_size > 0:
        e = int(bits[regime_size + 1:regime_size + 1 + es_size], 2)
    else:
        e = 0
    f = 1
    if p_size > regime_size + es_size + 1:
        f = bit2fraction(bits[regime_size + 1 + es_size:])

    # returns the real signed number
    return s * f * pow(2, e) * pow(pow(2, pow(2, es_size)), k)


# function: convert a string representing a hexadecimal number in a binary number
def hex2bit(hex_in, expected_len):
    # $ parameters $
    # $hex_in: the string representing a hexadecimal number
    # $expected_len: the number of binary on which the output is required (zero padding if required)
    # returns the number converted in a binary string, with zeroes on the right if necessary
    return bin(int(hex_in, 16))[2:].zfill(expected_len)


# TODO: NOT WORKING FOR NEGATIVE NUMBERS
# function: convert a real number in a string of bit representing a posit
def real2posit(real: float, p_size, es_size):
    # $ parameters $
    # $real: [float] real number to be converted
    # $p_size: the number of bits on which the number $bits is represented
    # $es_size: the number of bits reserved for the posit exponent
    if real == 0:
        return 0, -p_size + 1, 1, 1
    p_bit = [0] * p_size
    r_bit = []
    fraction_bit = []
    e = 1
    s = 0
    f = 0
    if real < 0:
        s = 1
    k = 0

    # calculate K
    if real > 0:
        if real > 1:
            while pow(pow(2, pow(2, es_size)), k + 1) <= real:
                k += 1
        else:  # real in [0,1]
            while pow(pow(2, pow(2, es_size)), k) > real:
                k -= 1
    else:
        if real < -1:
            while -pow(pow(2, pow(2, es_size)), k + 1) >= real:
                k += 1
        else:  # real in [-1,0]
            while -pow(pow(2, pow(2, es_size)), k) < real:
                k -= 1

    # calculate exponent
    # real /= pow(2, e)

    # calculate fractional part
    f = abs(real) / pow(pow(2, pow(2, es_size)), k)
    fraction = f

    # convert fraction to binary
    for i in range(p_size - len(r_bit) - es_size):
        if fraction == 0:
            break
        if fraction >= pow(2, -i):
            fraction_bit += [1]
            fraction -= pow(2, -i)
        else:
            fraction_bit += [0]

    # padding
    while len(fraction_bit) + es_size + len(r_bit) < p_size:
        fraction_bit += [0]

        # build regime
    if real > 0:
        if k >= 0:
            for _ in range(k + 1):
                r_bit += [1]
        else:  # k < 0
            for _ in range(-k):
                r_bit += [0]
    else:
        # real < 0:
        if k > 0:
            for _ in range(k + 1):
                r_bit += [0]
        else:  # k < 0
            for _ in range(-k):
                r_bit += [1]
            if k == 0:
                r_bit = [1]

        # regime terminal bit
    if r_bit[0] == 0:
        r_bit += [1]
    else:
        r_bit += [0]

        # negative numbers have k increased for 2^n
    if real < 0:
        if real == -pow(2, k):
            r_bit = r_bit[1:]

    # assemble the posit
    for i in range(p_size):
        if i > len(r_bit) + es_size:  # write fraction
            # first bit of fraction_bit is always 0, must be skipped
            p_bit[i] = fraction_bit[i - (len(r_bit) + es_size)]
        # if i > len(r_bit) :
        # write exponent

        else:
            if i > 0:  # write regime
                p_bit[i] = r_bit[i - 1]
            else:
                p_bit[0] = s  # write sign

    # convert array to string
    p_out = ""
    for b in p_bit:
        p_out += str(b)
    # returns the number as a binary string encoded in posit, and the parts to make it
    # remember to store the function result as posit,_,_,_ if you don't need the extra stuff
    return [[p_out], [s], [r_bit], [fraction_bit]], k, f, e


# check if a number is posit_representable using a lookup table
def isRepresentable(num, p_size, es_size):
    # $ parameters $
    # $num: float number that should be checked if representable
    # $p_size: the number of bits on which the number $bits is represented
    # $es_size: the number of bits reserved for the posit exponent
    global representable_numbers_cache
    if num in representable_numbers_cache:
        return True
    res = False
    with open(table_folder + "/posit_" + str(p_size) + "_" + str(es_size) + ".csv") as f:
        for line in f:
            row = line.rstrip()
            chunks = row.split(" ")
            if chunks[-1] == "NaR":
                continue
            f = float(chunks[-1])
            if num == f:
                # optional feature: save some numbers aside in order to have a chance to avoid reading the file again
                # useful if you have lots of repetitions, and large lookup table
                if cache_max_size > 0:
                    if cache_max_size < len(representable_numbers_cache):
                        representable_numbers_cache += [f]
                    if cache_max_size == len(representable_numbers_cache):
                        # if cache is full, remove the oldest element
                        representable_numbers_cache = representable_numbers_cache[1:]
                res = True
                # returns if True representable, false if not
    return res


# compute additions between two binary numbers
def binary_sum(max_size, b1, b2):
    # $ parameters $
    # max_size: length of strings b1 and b2
    # $b1: operand as a string
    # $b2: operand as a string
    res_reversed = []
    carry = 0
    res = ""
    a = 0
    b = 0
    for i in range(max_size).__reversed__():
        if i < len(b1):
            a = int(b1[i])
        if i < len(b2):
            b = int(b2[i])
        s = carry + a + b
        if s == 0:
            carry = 0
            res_reversed += [0]
        if s == 1:
            carry = 0
            res_reversed += [1]
        if s == 2:
            carry = 1
            res_reversed += [0]
        if s == 3:
            carry = 1
            res_reversed += [1]

    for c in res_reversed.__reversed__():
        if c == 1:
            res += "1"
        else:
            res += "0"

    while len(res) < max_size:
        res += "0"
    # return a string of bits representing the result
    return res


# compute subtractions between two binary numbers
def binary_diff(max_size, b1, b2):
    # $ parameters $
    # max_size: length of strings b1 and b2
    # $b1: operand as a string
    # $b2: operand as a string
    # returns the subctraction as a string of bits
    return binary_sum(max_size, b1, a2comp(b2, len(b2)))

