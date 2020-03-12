from __future__ import print_function
#
# Test the SVE ZReg reports the right amount of data. It uses the
# sve-ioctl test and examines the register data each time the
# __sve_ld_done breakpoint is hit.
#
# This is launched via tests/guest-debug/run-test.py
#

import gdb
import sys

initial_vlen = 0
failcount = 0

def report(cond, msg):
    "Report success/fail of test"
    if cond:
        print ("PASS: %s" % (msg))
    else:
        print ("FAIL: %s" % (msg))
        global failcount
        failcount += 1

class TestBreakpoint(gdb.Breakpoint):
    def __init__(self, sym_name="__sve_ld_done"):
        super(TestBreakpoint, self).__init__(sym_name)
        # self.sym, ok = gdb.lookup_symbol(sym_name)

    def stop(self):
        val_i = gdb.parse_and_eval('i')
        global initial_vlen
        try:
            for i in range(0, int(val_i)):
                val_z = gdb.parse_and_eval("$z0.b.u[%d]" % i)
                report(int(val_z) == i, "z0.b.u[%d] == %d" % (i, i))
            for i in range(i + 1, initial_vlen):
                val_z = gdb.parse_and_eval("$z0.b.u[%d]" % i)
                report(int(val_z) == 0, "z0.b.u[%d] == 0" % (i))
        except gdb.error:
            report(False, "checking zregs (out of range)")


def run_test():
    "Run through the tests one by one"

    print ("Setup breakpoint")
    bp = TestBreakpoint()

    global initial_vlen
    vg = gdb.parse_and_eval("$vg")
    initial_vlen = int(vg) * 8

    gdb.execute("c")

#
# This runs as the script it sourced (via -x, via run-test.py)
#
try:
    inferior = gdb.selected_inferior()
    if inferior.was_attached == False:
        print("SKIPPING (failed to attach)", file=sys.stderr)
        exit(0)
    arch = inferior.architecture()
    report(arch.name() == "aarch64", "connected to aarch64")
except (gdb.error, AttributeError):
    print("SKIPPING (not connected)", file=sys.stderr)
    exit(0)

try:
    # These are not very useful in scripts
    gdb.execute("set pagination off")
    gdb.execute("set confirm off")

    # Run the actual tests
    run_test()
except:
    print ("GDB Exception: %s" % (sys.exc_info()[0]))
    failcount += 1
    import code
    code.InteractiveConsole(locals=globals()).interact()
    raise

print("All tests complete: %d failures" % failcount)
exit(failcount)