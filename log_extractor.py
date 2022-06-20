# python decoder for output.log
from os import listdir
from os.path import isfile, join
from simplePositLib import *

# ---------------------------------------------------------------
# ----------------------- CONFIGURATION -------------------------
verbose = True  # output more data to console; True => VERY SLOW to execute
show_progress = True  # output in console how many lines have been read
path = 'logs'  # folder containing the .log files
rounding_tolerance = 1  # how many consecutive posits are considered a correct approximation
limit_rows_per_file = -1  # max lines per file to read; put -1 to read the whole file.
limit_errors_to_display = 50  # max errors to output in console as samples; put -1 for infinite
input_type = "bin"  # "bin" or "hex" to select if log file contains binary or hexadecimals
output_type = "bin"  # "bin" or "hex" to select if log file contains binary or hexadecimals
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
Approx_ok = 0
Approx_no = 0
Discarded = 0
last_msg = ""
errors_displayed = 0
last_line_read = 0


# ---------------------------------------------------------------
# ------------------------- FUNCTIONS ---------------------------

# LOG file should be written with rows like: "'i' $input 'o' $output"
def extract_raw_input(raw_input):
    chunks = raw_input.split(' ')
    # chunks[1] is the input
    # the output is made with two parts: a flag (1 bit) + a vector (variable size)
    # chunks[3] is {flag[1],output[n]}
    return chunks[1], chunks[3][1:], chunks[3][0]


# input array is {A,B,C}
# output array has already been trimmed to remove the flag that was in head
# A,B,C,Out can be binary strings or hex strings
# returned values  must be binary strings
def split_variables(in_raw, out_raw):
    if input_type == "hex":
        a = hex2bit(in_raw[:A_h_len], A_binary_len)
        b = hex2bit(in_raw[A_h_len:A_h_len + B_h_len], B_binary_len)
        c = hex2bit(in_raw[A_h_len + B_h_len:], C_binary_len)
    else:
        a = in_raw[:A_binary_len]
        b = in_raw[A_binary_len:A_binary_len + B_binary_len]
        c = in_raw[A_binary_len + B_binary_len:]
    if output_type == "hex":
        o = hex2bit(out_raw, Out_binary_len)
    else:
        o = out_raw
    return a, b, c, o


# expected operation is A+B*C; the result is compared with the output saved in the log
def expected_output(a, b, c):
    return a + b * c


# sensitivity is the smallest number that can be computed
def calculate_error(a, b, c, o, sensitivity):
    e = o - expected_output(a, b, c)
    # returns the error, and a flag that notify is the number was not representable (smaller than sensitivity)
    return e, (abs(e) < sensitivity)


# fancy console messages
def verbose_msg(msg):
    if msg == "x":
        return "Line discarded because of 'x' flag\n"
    if msg == "a":
        return "Expected output not representable, but effective output is correctly rounded\n"
    if msg == "o":
        return "Expected output not representable, and effective output is not in rounding interval\n"
    if msg == "e":
        return "Output is wrong\n"
    if msg == "v":
        return "Output is correct\n"
    return "\n"


# read the log file line by line, and produce a validation report
def validate_log(input_file, max_lines=-1):
    # validation counters are initialized to zero
    global Correct
    global Read
    global Mistakes
    global Approx_ok
    global Approx_no
    global Discarded
    global verbose
    global last_msg
    global errors_displayed
    global last_line_read
    # the smallest number that can be represented with the number of bits of the output
    # a number smaller than this is considered not representable
    sensitivity = posit2real('1'.zfill(N))
    print("Starting: scan ", input_file)
    with open(path + "/" + input_file, "r") as f:
        # declare variables to keep the in scope
        a_b = 0
        b_b = 0
        c_b = 0
        out_b = 0
        a_f = 0
        b_f = 0
        c_f = 0
        out_f = 0
        e = 0
        for line in f:
            # avoid to read the whole file, that might be huge
            raw_input = line.rstrip()
            if last_line_read == raw_input:
                print("End of file reached")
                break
            # last line of the file might be incomplete
            if Read > 0:
                if len(last_line_read) != len(raw_input):
                    print("Incomplete line trimmed out")
                    break
            last_line_read = raw_input
            if max_lines == 0:
                print("Enforced shut down: reached limit of max lines for this file")
                break
            if max_lines > 0:
                max_lines -= 1

            # get input/output arrays, plus a flag
            in_vector, out_vector, flag = extract_raw_input(raw_input)

            # check correct size of input string
            if input_type == "hex":
                if len(in_vector) != A_h_len + B_h_len + C_h_len:
                    if verbose:
                        print("Invalid input arguments for line ", Read)
                    Discarded += 1
                    Read += 1
                    last_msg = "x"
            else:
                if len(in_vector) != A_binary_len + B_binary_len + C_binary_len:
                    if verbose:
                        print("Invalid input arguments for line ", Read)
                    Discarded += 1
                    Read += 1
                    last_msg = "x"
            # check correct size of output string
            if input_type == "hex":
                if len(out_vector) != Out_h_len:
                    if verbose:
                        print("Invalid output arguments for line ", Read)
                    Discarded += 1
                    Read += 1
                    last_msg = "x"
            else:
                if len(out_vector) != Out_binary_len:
                    if verbose:
                        print("Invalid output arguments for line ", Read)
                    Discarded += 1
                    Read += 1
                    last_msg = "x"
            # if the network was not ready to produce the output yet (usually the very first clock posedge)
            if flag == 'x':
                if verbose:
                    print("Invalid line ", Read)
                Discarded += 1
                Read += 1
                last_msg = "x"

            else:
                # cut the arrays into variables
                a_b, b_b, c_b, out_b = split_variables(in_vector, out_vector)
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
                        # the output cannot be represented, so the error is due to rounding
                        Approx_ok += 1
                        last_msg = "a"
                    else:
                        # output might be not representable
                        o_lb_f = posit2real(binary_diff(N, out_b, str(rounding_tolerance).zfill(N)), N,
                                            ES)
                        o_ub_f = posit2real(binary_sum(N, out_b, str(rounding_tolerance).zfill(N)), N, ES)

                        e_low, _ = calculate_error(a_f, b_f, c_f, o_lb_f, 0)
                        e_upp, _ = calculate_error(a_f, b_f, c_f, o_ub_f, 0)

                        # if the correct result is between two consecutive posit, then
                        # the error for them should have different sign

                        if sign(e) != sign(e_low):
                            Approx_ok += 1  # up rounding has happened
                            last_msg = "a"
                        else:
                            if sign(e) != sign(e_upp):
                                Approx_ok += 1  # down rounding has happened
                                last_msg = "a"
                            else:  # error is beyond approximation threshold
                                representable = isRepresentable(expected_output(a_f, b_f, c_f), N, ES)
                                if representable:
                                    Mistakes += 1
                                    last_msg = "e"
                                else:
                                    Approx_no += 1
                                    last_msg = "o"

                else:
                    # the output can be represented and it is correct
                    Read += 1
                    Correct += 1
                    last_msg = "v"
            if show_progress and Read % 1000 == 0:
                print("Reached line ", Read)
            if verbose or ((last_msg == "e") and (errors_displayed < limit_errors_to_display)):
                print("Line: ", str(Read))
                if last_msg != "x":
                    print("A: ", a_b, " -> ", a_f)
                    print("B: ", b_b, " -> ", b_f)
                    print("C: ", c_b, " -> ", c_f)
                    print("Out: ", out_b, " -> ", out_f)
                    print(out_f, " = ", a_f, " + ", b_f * c_f, " + error")
                    print("Error: " + str(e))
                print("Decision: ", verbose_msg(last_msg))
                if last_msg == "e":
                    errors_displayed += 1
        f.close()
        print("Scan completed")


# ---------------------------------------------------------------
# ------------------------- MAIN BODY ---------------------------
for file in files:
    validate_log(file, limit_rows_per_file)

# validation report
print("\n ========= Analysis completed ========= ")
print("# Lines read: " + str(Read))
print("# Discarded lines: " + str(Discarded))
print("\n # Representable output: ", str(Correct + Mistakes))
print("Correct results: " + str(Correct))
print("Mistakes: " + str(Mistakes))
print("\n # Not representable output: ", str(Approx_ok + Approx_no))
print("Approximation radius: ", rounding_tolerance, " consecutive posits")
print("Correctly approximated: " + str(Approx_ok))
print("Wrongly approximated: " + str(Approx_no))
