#!/usr/bin/env python3
# Author: Emmanuel Odeke <odeke@ualberta.ca>

import sys
from optparse import OptionParser

import restDriver

EOF  = ''
EXIT = 'exit'
HELP = 'help'

translator = dict(
    bcksum      = ['getCheckSum', 'binaryData', 'algoName'],
    fcksum      = ['getFileCheckSum', 'path', 'algoName'],
    list        = ['getCloudFilesManifest', 'query'],
    pull        = ['downloadBlob', 'key'],
    push        = ['uploadBlob', 'srcPath'],
    putFile     = ['updateFile', 'key', 'attrs'],
    putBlob     = ['updateStream', 'stream'],
    sign        = ['signItems', '*'],
    trash       = ['deleteBlob', 'attrs'],
    updateSecretKey = ['updateSecretKey', 'secretKey'],
)


def tokenizer(line):
    splits = line.strip('\n').split(' ')
    splits = [field for field in splits if field]
    if len(splits) < 1:
        return '', ''

    cmd, *rest = splits

    cmd_l = cmd.lower()

    if cmd_l == EXIT:
        return sys.exit(0)
    if cmd_l == HELP:
        return show_help()

    resolve = translator.get(cmd_l, None)
    if resolve is None:
        raise Exception(cmd_l)

    equivCmd, resolveRest = resolve[0], resolve[1:]
    args = {}
    resolveRestLen = len(resolveRest)
    for i, arg in enumerate(rest):
        if i >= resolveRestLen:
            break

        equivalent = resolveRest[i]
        args[equivalent] = arg

    return equivCmd, args

def get_line(f):
    write(sys.stdout, "$ ")
    return f.readline()

def apply_f(restD, equivCmd, argDict):
    cmd = getattr(restD, equivCmd, None)
    if cmd is None:
        raise Exception(cmd)

    return cmd(**argDict)

def write(f, *args):
    f.write(' '.join(str(arg) for arg in args)) and f.flush()

def write_line(f, *args):
    write(f, *args)
    write(f, '\n')

def show_help():
    write(sys.stdout, '**\n')
    for k, v in translator.items():
        write(sys.stdout, '\n%s:\n %s\n**\n'%(k, ' '.join(v)))
    return '', ''

def main():
    restObj = restDriver.RestDriver(ip='http://192.168.1.112')
    while 1:
        line_in = get_line(sys.stdin)
        if line_in == EOF:
            return
        cmd, argDict = tokenizer(line_in)
        if cmd:
            write_line(sys.stdout, apply_f(restObj, cmd, argDict))

if __name__ == '__main__':
    main()
