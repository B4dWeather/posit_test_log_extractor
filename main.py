# python decoder for output.log
from os import listdir
from os.path import isfile, join

limit = 25
# parameter to work:
N = 8
ES = 0
# expected input size:
A_binary_len = N * 2
B_binary_len = N
C_binary_len = N
Out_binary_len = N
# expected hex size:
A_h_len = int(A_binary_len / 4)
B_h_len = int(B_binary_len / 4)
C_h_len = int(C_binary_len / 4)
Out_h_len = int(Out_binary_len / 4)
# dataset files
path = 'logs'
files = [f for f in listdir(path) if isfile(join(path, f))]


def a2comp(bits, expected_len=8):
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
    return converted[2:].zfill(expected_len)


def regime(posit_bits, size):
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
    return m, i


def bit2fraction(bits):
    f = 1
    i = 1
    for bit in bits:
        if bit == '1':
            f += pow(2, -1 * i)
        i += 1
    return f


def bit2posit(bits, p_size=8, es_size=0):
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
    return s * f * pow(2, e) * pow(pow(2, pow(2, es_size)), k)


def hex2bit(hex_in, expected_len):
    return bin(int(hex_in, 16))[2:].zfill(expected_len)


def extract_raw_input(raw_input):
    chunks = raw_input.split(' ')
    return chunks[1], chunks[3][1:], chunks[3][0]


def split_variables(in_hex, out_hex):
    a = hex2bit(in_hex[:A_h_len], A_binary_len)
    b = hex2bit(in_hex[A_h_len:A_h_len + B_h_len], B_binary_len)
    c = hex2bit(in_hex[A_h_len + B_h_len:], C_binary_len)
    o = hex2bit(out_hex, Out_binary_len)
    return a, b, c, o


def validate_log(input_file, max_lines=-1):
    with open(path + "/" + input_file, "r") as file:
        for line in file:

            raw_input = line.rstrip()

            if max_lines == 0:
                break
            else:
                if max_lines > 0:
                    max_lines -= 1

            in_hex, out_hex, flag = extract_raw_input(raw_input)

            if flag == 'x':
                continue

            a_b, b_b, c_b, out_b = split_variables(in_hex, out_hex)

            a_f = bit2posit(a_b)
            b_f = bit2posit(b_b)
            c_f = bit2posit(c_b)
            out_f = bit2posit(out_b)

    file.close()


validate_log(files[0], 5)
