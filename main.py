# python decoder for output.log
from os import listdir
from os.path import isfile, join
from simplePositLib import *

# ---------------------------------------------------------------
# ----------------------- CONFIGURATION -------------------------
verbose = False  # output more data to console; True => VERY SLOW to execute
path = 'logs'  # folder containing the .log files
limit = 500001  # max lines per file to read; put -1 to read the whole file.
# parameter to work with:
N = 8  # bits on which each posit is allocated
ES = 0  # bits reserved for exponent, in a posit string
# ---------------------------------------------------------------
# ------------------------- PARAMETERS --------------------------
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
files = [f for f in listdir(path) if isfile(join(path, f))]
# ---------------------------------------------------------------
# ------------------------- VARIABLES ---------------------------
# statistics
Correct = 0
Mistakes = 0
Read = 0
Approx = 0
Discarded = 0
last_msg = ""


# ---------------------------------------------------------------
# ------------------------- FUNCTIONS ---------------------------

# LOG file should be written with rows like: "'i' $input 'o' $output"
def extract_raw_input(raw_input):
    chunks = raw_input.split(' ')
    # the output is made with two parts: a flag (1 bit) + a vector (variable size)
    # chunks[1] is the input
    # chunks[3] is {flag[1],output[n]}
    return chunks[1], chunks[3][1:], chunks[3][0]


# input array is {A,B,C}
# output array has already been trimmed to remove the flag that was in head
def split_variables(in_hex, out_hex):
    a = hex2bit(in_hex[:A_h_len], A_binary_len)
    b = hex2bit(in_hex[A_h_len:A_h_len + B_h_len], B_binary_len)
    c = hex2bit(in_hex[A_h_len + B_h_len:], C_binary_len)
    o = hex2bit(out_hex, Out_binary_len)
    return a, b, c, o


# expected operation is A+B*C; the result is compared with the output saved in the log
# sensitivity is the smallest number that can be computed
def calculate_error(a, b, c, o, sensitivity):
    e = o - (a + b * c)
    # returns the error, and a flag that notify is the number was not representable (smaller than sensitivity)
    return e, (abs(e) < sensitivity)


# fancy console messages
def verbose_msg(msg):
    if msg == "x":
        return "Line discarded because of 'x' flag"
    if msg == "a":
        return "Expected output not representable, but effective output is correctly rounded"
    if msg == "e":
        return "Output is wrong"
    if msg == "v":
        return "Output is correct"
    return ""


# read the log file line by line, and produce a validation report
def validate_log(input_file, max_lines=-1):
    # validation counters are initialized to zero
    global Correct
    global Read
    global Mistakes
    global Approx
    global Discarded
    global verbose
    global last_msg
    # the smallest number that can be represented with the number of bits of the output
    # a number smaller than this is considered not representable
    sensitivity = posit2real('1'.zfill(N))

    print("Starting: scan ", input_file)
    with open(path + "/" + input_file, "r") as f:

        a_f = 0
        b_f = 0
        c_f = 0
        out_f = 0
        e = 0
        for line in f:
            # avoid to read the whole file, that might be huge
            raw_input = line.rstrip()

            if max_lines == 0:
                print("Enforced shut down: reached limit of max lines for this file")
                break
            if max_lines > 0:
                max_lines -= 1
            # get input/output arrays as hexadecimals, plus a flag
            in_hex, out_hex, flag = extract_raw_input(raw_input)

            # if the network was not ready to produce the output yet (usually the very first clock posedge)
            if flag == 'x':
                Discarded += 1
                Read += 1
                last_msg = "x"
            else:
                # cut the arrays into variables
                a_b, b_b, c_b, out_b = split_variables(in_hex, out_hex)
                # convert hex variables into binary variables, then to real variables
                a_f = posit2real(a_b, 2 * N, ES)
                b_f = posit2real(b_b, N, ES)
                c_f = posit2real(c_b, N, ES)
                out_f = posit2real(out_b, N, ES)

                # compare output and expected output
                e, negligible = calculate_error(a_f, b_f, c_f, out_f, sensitivity)

                if e != 0:
                    Read += 1
                    if negligible:
                        # ethe output cannot be represented, so the error is due to rounding
                        Approx += 1
                        last_msg = "a"
                    else:
                        # output might be not representable

                        if e > 0:  # round up happened, o > a+bc
                            o_lb_f = posit2real(bin(int(out_b, 2) - 1), N, ES)
                            e2, _ = calculate_error(a_f, b_f, c_f, o_lb_f, 0)
                            if e2 < 0:  # the correct result is not between two consecutive posit
                                Approx += 1  # so it is rounded
                                last_msg = "a"
                            else:
                                Mistakes += 1  # or, it is just wrong
                                last_msg = "e"
                        else:  # round down happened, o < a+bc
                            o_ub_f = posit2real(bin(int(out_b, 2) + 1), N, ES)
                            e2, _ = calculate_error(a_f, b_f, c_f, o_ub_f, 0)
                            if e2 > 0:  # the correct result is not between two consecutive posit
                                Approx += 1  # so it is rounded
                                last_msg = "a"
                            else:
                                Mistakes += 1  # or, it is just wrong
                                last_msg = "e"
                        # output can be represented but it is wrong
                        Mistakes += 1
                        last_msg = "e"
                else:
                    # the output can be represented and it is correct
                    Read += 1
                    Correct += 1
                    last_msg = "v"
            if Read % 1000 == 0:
                print("Reached line ", Read)
            if verbose:
                print("Line: ", str(Read))
                print("A: ", a_f, "B: ", b_f, " C: ", c_f, f" Out: ", out_f)
                print(out_f, " = ", a_f, " + ", b_f * c_f)
                print("Error: " + str(e))
                print("Decision: ", verbose_msg(last_msg))
        f.close()
        print("Scan completed")

        # ---------------------------------------------------------------


# ------------------------- MAIN BODY ---------------------------
for file in files:
    validate_log(file, limit)

# validation report
print("lines read: " + str(Read))
print("correct: " + str(Correct))
print("Correctly approximated: " + str(Approx))
print("mistakes: " + str(Mistakes))
print("Discarded lines: " + str(Discarded))
