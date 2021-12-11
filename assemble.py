import sys
import json

if len(sys.argv) != 3:
    print("Usage: python3 assemble.py <in.bfasm> <out.bf>")
    sys.exit(1)


with open(sys.argv[1]) as f:
    asm = f.read()

# preproccesor
replace = {}
for line in asm.split('\n'):
    if line.startswith('#'):
        parsedLine = line[1:].split(' ')
        command = parsedLine[0]
        if command == 'define':
            replace[parsedLine[1]] = parsedLine[2]
        elif command == 'include':
            with open(parsedLine[1]) as f:
                asm += f.read()

for item in replace:
    asm = asm.replace(item, replace[item])


compiled = ""

parseDict = {}
currentItem = ""
for line in asm.split('\n'):
    if line == '' or line[0] == '#':
        continue

    # comments
    if line.strip().startswith(';'):
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
occupied = []
def goMem(n):
    global currentPtr
    result = getMem(n) - currentPtr
    currentPtr += result
    print(f'\033[35mgoMem({n}) ->\033[96m', '>' * result + '<' * -result, '\033[0m')
    return '>' * result + '<' * -result

def getMem(n):
    print(f'getMem({n})')
    global mem
    n = n[1:]
    if n in mem:
        return mem[n]
    else:
        print('\033[31mgetMem Error\033[0m: memory not allocated')
        sys.exit(1)

def allocMem(*args):
    print(f'allocMem({args})')
    global mem
    for n in args:
        n = n[1:]
        print('allocating', repr(n))
        if n in mem:
            print('\033[31mallocMem Error\033[0m: memory already allocated')
            sys.exit(1)
        x = 0
        while x in occupied:
            x += 1
        mem[n] = x
        occupied.append(x)
    print('after alloc:', mem)

def freeMem(*args):
    print(f'freeMem({args})')
    global mem
    for n in args:
        n = n[1:]
        if n not in mem:
            print('\033[31mfreeMem Error\033[0m: memory not allocated')
            sys.exit(1)
        occupied.remove(mem[n])
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
        elif item.startswith('%'):
            result.append(args[parseDict[funcName]['args'].index(item)])
        elif item.startswith('$'):
            result.append(int(item[1:]))
        elif item.startswith('#'):
            try:
                parsedLine.append(parseDict['def'][x])
            except KeyError:
                print('\033[31mError\033[0m: undefined label', x)
                sys.exit(1)
        else:
            result.append(item)
    print('\033[32mdebug parseArgs (pass2):', repr(result), '\033[0m')
    result = [x for x in result if x != '']
    return result

lineTokens = '*+">'
lineSeps = ' '
def parseLine(funcStack, funcName, line, args):
    global currentPtr
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
            '''
            print('debug:')
            print('lastItem:', lastItem)
            print('lastOp:', lastOp)
            print('current:', current)
            print('inbf:', inbf)
            print('item:', item)
            print()
            '''
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
                current += lastItem
                lastItem = ''
                current += goMem(item)
            else:
                print('\033[31mError\033[0m: injection panic :(')
                print('item:', item)
                sys.exit(1)
        current += lastItem
        print('inject compiled:\033[96m', current, '\033[0m')
        compiled += current

    # free mem
    elif parsedLine[0] == 'free':
        freeMem(*parsedLine[1:])

    # alloc mem
    elif parsedLine[0] == 'alloc':
        allocMem(*parsedLine[1:])

    # while
    elif parsedLine[0] == 'while':
        compiled += goMem(parsedLine[1])
        compiled += '['
        enterFunc(funcStack, parsedLine[2], parsedLine[3:])
        compiled += goMem(parsedLine[1])
        compiled += ']'

    # occupy
    elif parsedLine[0] == 'occ':
        if len(parsedLine) != 3:
            print('\033[31mError\033[0m: wrong number of arguments for occupy')
            sys.exit(1)
        x = 0
        while not all(y not in occupied for y in range(x, x + parsedLine[2])):
            x += 1
            
        print('\033[36moccupy\033[0m:', x, '->', x + parsedLine[2])
        mem[parsedLine[1][1:]] = x
        occupied.extend(range(x, x + parsedLine[2]))

    # unoccupy
    elif parsedLine[0] == 'uoc':
        if len(parsedLine) != 3:
            print('\033[31mError\033[0m: wrong number of arguments for unoccupy')
            sys.exit(1)
        for x in range(mem[parsedLine[1][1:]], parsedLine[2]):
            occupied.remove(x)
        freeMem((parsedLine[1]))

    # ptr
    elif parsedLine[0] == 'ptr':
        if len(parsedLine) != 2:
            print('\033[31mError\033[0m: wrong number of arguments for ptr')
            sys.exit(1)
        currentPtr += parsedLine[1]

    else:
        print('\033[31mError\033[0m: unknown command')
        sys.exit(1)

    print('\033[33mMEMORY\033[0m:', mem)
    print('\033[33mOCCUPIED\033[0m:', occupied)
    print('\033[33mCURRENTPTR\033[0m:', currentPtr)

            

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
print('\033[96m'+compiled+'\033[0m')

with open(sys.argv[2], 'w') as f:
    f.write(compiled)
