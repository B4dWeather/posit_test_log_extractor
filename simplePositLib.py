# ---------------------------------------------------------------
# ---------------------------------------------------------------
# Simple python library for some posit operations
# Usage Example:
#   # put your posit (which you have in HEX) in a variable
#   in_hex = some posit number, represented as HEX on N/4 digits
#   # you can convert it in binary
#   pp_bin = hex2bit(in_hex, N)
#   # you can convert it in real
#   pp_real = posit2real(pp_bin,N,ES) #ES is the number of exponent bits
# ---------------------------------------------------------------
# ---------------------------------------------------------------
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


# function: compute the regime of the given Posit
def regime(posit_bits, size):
    # $ parameters $
    # $posit_bits: posit number codified as a binary string
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
    s = 1
    if bits[0] == '1':
        s = -1
    if s < 0:
        bits = a2comp(bits, p_size)
    k, regime_size = regime(bits, p_size)
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
