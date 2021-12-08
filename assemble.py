import sys
import json
import re

if len(sys.argv) != 3:
    print("Usage: python3 assemble.py <in.bfasm> <out.bf>")
    sys.exit(1)

with open(sys.argv[1]) as f:
    asm = f.read()

compiled = ""

parseDict = {}
currentItem = ""
for line in asm.split('\n'):
    if line == '':
        continue

    if line.startswith(' '*4):
        parseDict[currentItem]['body'] += [line.strip()]
    elif line.startswith('.'):
        parseDict[line.split(' ')[0]] = {'args':line.split(' ')[1:], 'type':'func', 'body':[]}
        currentItem = line.split(' ')[0]
    elif line.startswith('-'):
        parseDict[line.split(' ')[0]] = {'args':line.split(' ')[1:], 'type':'multiFunc', 'body':[]}
        currentItem = line.split(' ')[0]
    else:
        print('\033[31mError\033[0m: ' + line)

print('parseDict:')
print(json.dumps(parseDict, indent=4))
print()

currentPtr = 0
mem = {}
def goMem(n, funcStack):
    print(f'goMem({n}, {funcStack})')
    global currentPtr
    result = currentPtr - getMem(n, funcStack)
    currentPtr = result
    return '>' * result + '<' * -result

def getMem(n, funcStack):
    print(f'getMem({n}, {funcStack})')
    global mem
    n = n[1:]
    if n.startswith('@'):
        n = funcStack+' '+n[1:]
    if n in mem:
        return mem[n]
    elif n in funcStack:
        return funcStack[n]
    else:
        print('\033[31mError\033[0m: memory not allocated')
        sys.exit(1)

def allocMem(*args, funcStack):
    print(f'allocMem({args}, {funcStack})')
    global mem
    for n in args:
        n = n[1:]
        if n.startswith('@'):
            n = funcStack+' '+n[1:]
        print('allocating', repr(n))
        if n in mem:
            print('\033[31mError\033[0m: memory already allocated')
            sys.exit(1)
        x = 0
        while x in mem:
            x += 1
        mem[n] = x
    print('after alloc:', mem)

def freeMem(*args, funcStack):
    print(f'freeMem({args}, {funcStack})')
    global mem
    for n in args:
        n = n[1:]
        if n.startswith('@'):
            n = funcStack+' '+n[1:]
        if n not in mem:
            print('\033[31mError\033[0m: memory not allocated')
            sys.exit(1)
        del mem[n]

def parseArgs(funcStack, funcName, line, args):
    parsedLine = ['']
    inInj = False
    totalQuotes = 0
    for x in line:
        if x == '{':
            parsedLine.append('{')
            parsedLine.append('')
            inInj = True
        elif x == '}':
            parsedLine.append('}')
            parsedLine.append('')
            inInj = False
        elif x == '"':
            totalQuotes += 1
            parsedLine.append(x)
            parsedLine.append('')
        elif inInj:
            parsedLine[-1] += x
        elif x in lineTokens:
            parsedLine.append(x)
            parsedLine.append('')
        elif x in lineSeps:
            if totalQuotes % 2 == 0:
                parsedLine.append('')
            else:
                parsedLine[-1] += x
        else:
            parsedLine[-1] += x
    print('\033[32mdebug parseArgs (pass1):', repr(parsedLine), '\033[0m')
    parsedLine = [x for x in parsedLine if x != '']
    result = ['']
    inStr = False
    for item in parsedLine:
        if item == '"':
            inStr = not inStr
        elif type(item) == int:
            result.append(item)
        elif inStr:
            for x in item:
                result.append(ord(x))
        elif item.startswith('#'):
            result.append(int(item[1:]))
        elif item.startswith('%'):
            result.append(args[parseDict[funcName]['args'].index(item)])
        elif item.startswith('@@'):
            result.append('@'+funcStack+' '+item[2:])
        else:
            result.append(item)
    print('\033[32mdebug parseArgs (pass2):', repr(result), '\033[0m')
    result = [x for x in result if x != '']
    return result

lineTokens = '*+">'
lineSeps = ' '
def parseLine(funcStack, funcName, line, args):
    global compiled
    if line.count('"') % 2 != 0:
        print('\033[31mError\033[0m: unclosed string :(')
        sys.exit(1)
    parsedLine = parseArgs(funcStack, funcName, line, args)

    print('func:', funcName)
    print('args:', args)
    print('line:', parsedLine)
    print()

    # entering function
    if parsedLine[0] in parseDict:
        if parsedLine[0] in funcStack.split(' '):
            print('\033[31mError\033[0m: recursive function call')
            sys.exit(1)

        enterFunc(funcStack, parsedLine[0], parsedLine[1:])

    # injecting
    elif parsedLine[0] == '>':
        lastItem = ''
        lastOp = ''
        current = ''
        inbf = False
        for item in parsedLine[1:]:
            #print('debug:')
            #print('lastItem:', lastItem)
            #print('lastOp:', lastOp)
            #print('current:', current)
            #print('inbf:', inbf)
            #print('item:', item)
            #print()
            if item == '{':
                current += lastItem
                lastItem = ''
                inbf = True
            elif item == '}':
                inbf = False
            elif inbf:
                lastItem += item
                if item in '<>':
                    print('\033[93mWARNING\033[0m: < or > in injection could fuck over the memory allocation system')
            elif item == '*':
                lastOp = '*'
            elif type(item) == int:
                if lastOp == '*':
                    current += lastItem * item
                    lastItem = ''
                else:
                    current += item
            elif item.startswith('@'):
                current += goMem(item, funcStack)
            else:
                print('\033[31mError\033[0m: injection panic :(')
                sys.exit(1)
        current += lastItem
        compiled += current

    # free mem
    elif parsedLine[0] == 'free':
        freeMem(*parsedLine[1:], funcStack=funcStack)

    # alloc mem
    elif parsedLine[0] == 'alloc':
        allocMem(*parsedLine[1:], funcStack=funcStack)

    else:
        print('\033[31mError\033[0m: unknown command')
        sys.exit(1)

            

def enterFunc(funcStack, funcName, args):
    print('enterFunc:', funcName)
    print('funcStack:', funcStack)
    func = parseDict[funcName]
    if func['type'] == 'multiFunc':
        if len(args) % len(func['args']) != 0:
            print('\033[31mError\033[0m: multiFunc has wrong modulo length arguments')
            sys.exit(1)
        for i in range(0, len(args), len(func['args'])):
            for line in func['body']:
                parseLine(funcStack + ' ' + funcName, funcName, line, args[i:i+len(func['args'])])
    elif func['type'] == 'func':
        if len(args) != len(func['args']):
            print('\033[31mError\033[0m: func has wrong number of arguments')
            sys.exit(1)
        for line in func['body']:
            parseLine(funcStack + ' ' + funcName, funcName, line, args)


enterFunc('', '.start', [])

print('compiled:')
print(repr(compiled))

with open(sys.argv[2], 'w') as f:
    f.write(compiled)
