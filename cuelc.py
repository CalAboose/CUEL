import sys
import os
import struct
import re


def init_tokens():
    errm_main = "misplaced MAIN's definition"
    errm_func = "missing an empty line before function definition"
    errm_nline = "misplaced empty line"
    errm_fcall = "function call out of scope"
    errm_end = "unexpected end of file"

    chkl_main = (False, ("begin"))
    chkl_func = (False, ("new-line"))
    chkl_nline = (True, ("new-line", "begin", "main", "func"))
    chkl_fcall = (True, ("new-line", "begin"))

    return (
        Token("begin", "(?!)", [], (), "", cdef),
        Token("end", "c^", [0xFF000000], chkl_nline, errm_end, cdef),

        Token("string", "^ {8}\"(.*)\"\n$", [], chkl_fcall, errm_fcall, cstr),
        Token("number", "^ {8}([0-9]{1,10})\n$", [], chkl_fcall, errm_fcall, cnum),
        Token("main", "^MAIN:\n$", [], chkl_main, errm_main, cmain),
        Token("func", "^([A-Z]([A-Z0-9-]{,45}[A-Z0-9]){,1}):\n$", [], chkl_func, errm_func, cfunc),

        Token("new-line", "^\n$", [0xFF000000], chkl_nline, errm_nline, cdef),

        Token("cal", "^ {8}cal ([A-Z]([A-Z0-9-]*[A-Z0-9])*)\n$", [0x00000000, 0xFE000000], chkl_fcall, errm_fcall, ccalls),
        Token("caz", "^ {8}caz ([A-Z]([A-Z0-9-]*[A-Z0-9])*)\n$", [0x00000000, 0xFD000000], chkl_fcall, errm_fcall, ccalls),
        Token("cnz", "^ {8}cnz ([A-Z]([A-Z0-9-]*[A-Z0-9])*)\n$", [0x00000000, 0xFC000000], chkl_fcall, errm_fcall, ccalls),
        Token("cgz", "^ {8}cgz ([A-Z]([A-Z0-9-]*[A-Z0-9])*)\n$", [0x00000000, 0xFB000000], chkl_fcall, errm_fcall, ccalls),
        Token("clz", "^ {8}clz ([A-Z]([A-Z0-9-]*[A-Z0-9])*)\n$", [0x00000000, 0xFA000000], chkl_fcall, errm_fcall, ccalls),

        Token("swp", "^ {8}swp\n$", [0xF9000000], chkl_fcall, errm_fcall, cdef),
        Token("swx", "^ {8}swx\n$", [0xF8000000], chkl_fcall, errm_fcall, cdef),
        Token("rcw", "^ {8}rcw\n$", [0xF7000000], chkl_fcall, errm_fcall, cdef),
        Token("rcc", "^ {8}rcc\n$", [0xF6000000], chkl_fcall, errm_fcall, cdef),

        Token("pop", "^ {8}pop\n$", [0xF5000000], chkl_fcall, errm_fcall, cdef),
        Token("dup", "^ {8}dup\n$", [0xF4000000], chkl_fcall, errm_fcall, cdef),

        Token("neg", "^ {8}neg\n$", [0xF3000000], chkl_fcall, errm_fcall, cdef),
        Token("+", "^ {8}\+\n$", [0xF2000000], chkl_fcall, errm_fcall, cdef),
        Token("*", "^ {8}\*\n$", [0xF1000000], chkl_fcall, errm_fcall, cdef),
        Token("/", "^ {8}/\n$", [0xF0000000], chkl_fcall, errm_fcall, cdef),
        Token("-", "^ {8}-\n$", [0xEF000000], chkl_fcall, errm_fcall, cdef),
        Token("%", "^ {8}%\n$", [0xEE000000], chkl_fcall, errm_fcall, cdef),

        Token("getn", "^ {8}getn\n$", [0xED000000], chkl_fcall, errm_fcall, cdef),
        Token("putn", "^ {8}putn\n$", [0xEC000000], chkl_fcall, errm_fcall, cdef),
        Token("puts", "^ {8}puts\n$", [0xEB000000], chkl_fcall, errm_fcall, cdef)
        )


class Token:
    def __init__(self, typ, rex, btc, chklist, errmsg, bcode):
        self.type = typ
        self.rex = rex
        self.btc = btc
        self.chklist = chklist
        self.errmsg = errmsg
        self.bcode = bcode


class Context:
    def __init__(self, ln, tokens, token, prevtok, fdefs, fcalls, bytecode, rexm):
        self.ln = ln
        self.tokens = tokens
        self.token = token
        self.prevtok = prevtok
        self.fdefs = fdefs
        self.fcalls = fcalls
        self.bytecode = bytecode
        self.rexm = rexm


def cdef(ctx):
    ctx.bytecode.extend(ctx.token.btc)


def cmain(ctx):
    ctx.fdefs["MAIN"] = len(ctx.bytecode)


def cfunc(ctx):
    fname = ctx.rexm.group(1)
    if fname in ctx.fdefs:
        raise SyntaxError("function redefinition")
    ctx.fdefs[fname] = len(ctx.bytecode)


def ccalls(ctx):
    fname = ctx.rexm.group(1)
    if fname not in ctx.fcalls:
        ctx.fcalls[fname] = []
    ctx.fcalls[fname].append((len(ctx.bytecode), ctx.ln))
    ctx.bytecode.extend(ctx.token.btc)


def cnum(ctx):
    num = int(ctx.rexm.group(1))
    if num >= 2**31:
        raise SyntaxError("number is out of range")
    ctx.bytecode.extend([num])


def pstr(s):
    sst = {'\\': '\\', 'n': '\n', 'r': '\r'}
    r, i = "", 0
    while i < len(s):
        c, d = s[i], 1
        if c == '\\' and i < len(s)-1:
            if s[i+1] in sst:
                c, d = sst[s[i+1]], 2
        r = r + c
        i += d
    return r


def cstr(ctx):
    sraw = ctx.rexm.group(1)
    s = pstr(sraw)
    btc = [0x00000000]
    for c in s[::-1]:
        btc.append(ord(c))
    ctx.bytecode.extend(btc)


def check_token(tok, prvtok):
    cin = tok.chklist[0]
    token_in = prvtok.type in tok.chklist[1]
    if cin and token_in or not (cin or token_in):
        raise SyntaxError(tok.errmsg)


def match_token(ctx, line):
    for tok in ctx.tokens:
        rexm = re.match(tok.rex, line)
        if rexm:
            return (tok, rexm)
    raise SyntaxError("unknown token")


def patch_btc(ctx):
    for fname, pss in ctx.fcalls.iteritems():
        if fname not in ctx.fdefs:
            raise SyntaxError("call to undefined function at line " + str(pss[0][1]))
        for pos in pss:
            ctx.bytecode[pos[0]] = ctx.fdefs[fname]


def parse_src(ctx, src_path, parse):
    with open(src_path) as fi:
        for line in fi:
            try:
                parse(ctx, line)
            except SyntaxError as e:
                raise SyntaxError(str(e) + " at line " + str(ctx.ln))


def parse_line(ctx, line):
    ctx.token, ctx.rexm = match_token(ctx, line)
    check_token(ctx.token, ctx.prevtok)
    ctx.token.bcode(ctx)

    ctx.prevtok = ctx.token
    ctx.ln += 1


def parse_end(ctx):
    ctx.token = ctx.tokens[1]
    check_token(ctx.token, ctx.prevtok)
    ctx.token.bcode(ctx)


def check_und(ctx):
    unused = set(ctx.fdefs)-set(["MAIN"])-set(ctx.fcalls)
    if unused != set():
        raise SyntaxError("unused functions - " + ", ".join(unused))


def write_btc(ctx, dst_path):
    with open(dst_path, 'wb') as fp:
        for btc in ctx.bytecode:
            fp.write(struct.pack('<I',btc))


def cuelpile(src_path, dst_path):
    try:
        tokens = init_tokens()
        ctx = Context(1, tokens, None, tokens[0], {}, {}, [0x4C455543], None)

        parse_src(ctx, src_path, parse_line)
        parse_end(ctx)
        check_und(ctx)
        patch_btc(ctx)
        write_btc(ctx, dst_path)
    except SyntaxError as e:
        print "Syntax error: {0}".format(e)
    except IOError as e:
        print "I/O error({0}): {1}".format(e.errno, e.strerror)


def get_file_name(path):
    rpath = re.match("^(.*[\/]){,1}([^\/]+)\.cuel$", path)
    if rpath:
        return rpath.group(2)
    return None


def main():
    if len(sys.argv) != 2:
        print "Usage: cuelc FILE"
        return

    src_path = sys.argv[1]
    if not os.path.exists(src_path):
        print "Source file not found."
        return

    file_name = get_file_name(src_path)
    if not file_name:
        print "Invalid source file name."
        return

    cuelpile(src_path, file_name + ".cuby")


if __name__ == "__main__":
    main()
