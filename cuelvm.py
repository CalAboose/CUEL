import sys
import os
import struct

def init_instrs():
    return {
        0xFF000000: eret,

        0xFE000000: ecal,
        0xFD000000: ecaz,
        0xFC000000: ecnz,
        0xFB000000: ecgz,
        0xFA000000: eclz,

        0xF9000000: eswp,
        0xF8000000: eswx,
        0xF7000000: ercw,
        0xF6000000: ercc,

        0xF5000000: epop,
        0xF4000000: edup,

        0xF3000000: eneg,
        0xF2000000: epls,
        0xF1000000: emul,
        0xF0000000: ediv,
        0xEF000000: emin,
        0xEE000000: emod,

        0xED000000: egetn,
        0xEC000000: eputn,
        0xEB000000: eputs
        }


class VmState:
    def __init__(self, ip, callstack, datastack):
        self.ip = ip
        self.cs = callstack
        self.ds = datastack


class CyclicStack:
    def __init__(self, errmsg):
        self._buffer = []
        self._errmsg = errmsg

    def _pop(self, i):
        try:
            return self._buffer.pop(i)
        except IndexError as e:
            raise IndexError(self._errmsg)

    def _get(self, i):
        try:
            return self._buffer[i]
        except IndexError as e:
            raise IndexError(self._errmsg)

    def top(self):
        return self._get(-1)

    def pop(self):
        return self._pop(-1)

    def push(self, val):
        self._buffer.append(val)

    def rotcw(self):
        top = self._pop(-1)
        self._buffer.insert(0, top)

    def rotcc(self):
        bot = self._pop(0)
        self._buffer.append(bot)

    def size(self):
        return len(self._buffer)


def eret(vms):
    vms.ip = vms.cs.pop()


def ecal(vms):
    vms.cs.push(vms.ip)
    vms.ip = vms.ds.pop()
    return True


def ecaz(vms):
    jmpaddr = vms.ds.pop()
    jmpcon = vms.ds.pop()
    if jmpcon == 0:
        vms.cs.push(vms.ip)
        vms.ip = jmpaddr
        return True


def ecnz(vms):
    jmpaddr = vms.ds.pop()
    jmpcon = vms.ds.pop()
    if jmpcon != 0:
        vms.cs.push(vms.ip)
        vms.ip = jmpaddr
        return True


def ecgz(vms):
    jmpaddr = vms.ds.pop()
    jmpcon = vms.ds.pop()
    if jmpcon > 0:
        vms.cs.push(vms.ip)
        vms.ip = jmpaddr
        return True


def eclz(vms):
    jmpaddr = vms.ds.pop()
    jmpcon = vms.ds.pop()
    if jmpcon < 0:
        vms.cs.push(vms.ip)
        vms.ip = jmpaddr
        return True


def eswp(vms):
    op2 = vms.ds.pop()
    op1 = vms.ds.pop()
    vms.ds.push(op2)
    vms.ds.push(op1)


def epop(vms):
    vms.ds.pop()


def ercw(vms):
    vms.ds.rotcw()


def ercc(vms):
    vms.ds.rotcc()


def edup(vms):
    vms.ds.push(vms.ds.top())


def eneg(vms):
    num = vms.ds.pop()
    vms.ds.push(-num)


def epls(vms):
    op2 = vms.ds.pop()
    op1 = vms.ds.pop()
    vms.ds.push(op1 + op2)


def emul(vms):
    op2 = vms.ds.pop()
    op1 = vms.ds.pop()
    vms.ds.push(op1 * op2)


def ediv(vms):
    op2 = vms.ds.pop()
    op1 = vms.ds.pop()
    vms.ds.push(op1 / op2)


def emin(vms):
    op2 = vms.ds.pop()
    op1 = vms.ds.pop()
    vms.ds.push(op1 - op2)


def emod(vms):
    op2 = vms.ds.pop()
    op1 = vms.ds.pop()
    vms.ds.push(op1 % op2)


def eswx(vms):
    op3 = vms.ds.pop()
    op2 = vms.ds.pop()
    op1 = vms.ds.pop()
    vms.ds.push(op3)
    vms.ds.push(op2)
    vms.ds.push(op1)


def egetn(vms):
    num = int(input())
    vms.ds.push(num)


def eputn(vms):
    num = vms.ds.pop()
    sys.stdout.write(str(num))


def eputs(vms):
    ichar = vms.ds.pop()
    while ichar > 0:
        sys.stdout.write(chr(ichar))
        ichar = vms.ds.pop()


def chk_ip(bytecode, ip):
    if ip >= len(bytecode):
        raise IndexError("IP out of bounds")


def exec_btc(bytecode):
    keymsg = "invalid instruction   [BTC={0:#010X}, IP={1:#010X}]"
    inpmsg = "invalid input value   [BTC={0:#010X}, IP={1:#010X}]"
    chrmsg = "invalid output value  [BTC={0:#010X}, IP={1:#010X}]"
    cserrmsg = "call stack access out of bounds"
    dserrmsg = "data stack access out of bounds"
    vms = VmState(1, CyclicStack(cserrmsg), CyclicStack(dserrmsg))
    vms.cs.push(-1)
    instab = init_instrs()
    try:
        while vms.ip > 0:
            chk_ip(bytecode, vms.ip)
            instr = bytecode[vms.ip]
            noinc = False
            if instr < 2**31:
                vms.ds.push(instr)
            else:
                noinc = instab[instr](vms)
            if not noinc:
                vms.ip += 1

        if vms.cs.size():
            print "\nExecution error: abnormal program termination"
    except IndexError as e:
        print "\nIndex error: {0}".format(e)
    except MemoryError as e:
        print "\nMemory error: {0}".format(e)
    except KeyError as e:
        print ("\nKey error: " + keymsg).format(instr, vms.ip)
    except ValueError as e:
        print ("\nValue error: " + chrmsg).format(instr, vms.ip)
    except SyntaxError as e:
        print ("\nSyntax error: " + inpmsg).format(instr, vms.ip)
    except NameError as e:
        print ("\nName error: " + inpmsg).format(instr, vms.ip)
    except KeyboardInterrupt as e:
        print "\nProgram terminated."


def parse_btc(btc):
    unpack = struct.unpack_from
    return [unpack("<I", btc, x)[0] for x in range(0, len(btc), 4)]


def load_btc(btc_path):
    with open(btc_path,"rb") as fi:
        return fi.read()


def main():
    if len(sys.argv) != 2:
        print "Usage: cuelvm FILE"
        return

    btc_path = sys.argv[1]
    if not os.path.exists(btc_path):
        print "File not found."
        return

    btc_data = load_btc(btc_path)
    if len(btc_data) < 3*4 or len(btc_data) % 4 != 0:
        print "Invalid bytecode file."
        return

    bytecode = parse_btc(btc_data)
    if bytecode[0] != 0x4C455543:
        print "Invalid bytecode file. Missing magic number."
        return

    exec_btc(bytecode)


if __name__ == "__main__":
    main()
