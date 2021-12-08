import sys
if len(sys.argv) < 3:
    print('Usage: python3 compileToPython.py <in.bf> <out.bfpy>')
    sys.exit()

with open(sys.argv[1]) as f:
    prog = f.read()


# easier to read with a function name
def heapType(string):
    return string[0]

# clean up

# remove non brainfuck characters
bfChars = '<>+-,.[]'
new = ''
for char in prog:
    if char in bfChars:
        new += char
prog = new

# heap repeatable characters
new = []
last = ''
repeatable = '><+-]'
for char in prog:
    if char in repeatable and last == char:
        new[-1] += char
    else:
        new += [char]
        last = char
prog = new

# i : input                     : variable
# m : memory array              : variable
# p : memory pointer            : variable
# a : memory no empty validator : method
# b : next input                : method

compiled = '''
import sys
i=' '.join(sys.argv[1:])
m=[]
p=0
def a():
    global m
    while p>=len(m):m+=[0]
a()
def b():
    global i
    if len(i)==0:return 0
    t=i[0];i=i[1:];return ord(t)
'''[1:]
silent = False
if '-s' in sys.argv:
    silent = True
# remove newline at start
indentLevel = 0
for x in prog:
    thisLine = ''
    thisChange = 0
    
    if heapType(x) == '+':
        thisLine = f'm[p]=(m[p]+{len(x)})%256'
        if not silent:
            print(f'COMPILE: + {len(x)}')

    if heapType(x) == '-':
        thisLine = f'm[p]=(m[p]-{len(x)})%256'
        if not silent:
            print(f'COMPILE: - {len(x)}')

    if heapType(x) == '>':
        thisLine = f'p+={len(x)};a()'
        if not silent:
            print(f'COMPILE: > {len(x)}')

    if heapType(x) == '<':
        thisLine = f'p-={len(x)};a()'
        if not silent:
            print(f'COMPILE: < {len(x)}')

    if heapType(x) == '.':
        thisLine = 'print(chr(m[p]), end=\'\')'
        if not silent:
            print(f'COMPILE: .')

    if heapType(x) == ',':
        thisLine = 'm[p]=b()'
        if not silent:
            print(f'COMPILE: ,')

    if heapType(x) == '[':
        thisLine = 'while m[p]:'
        thisChange = 1
        indentLevel += 1
        if not silent:
            print('COMPILE: [')

    if heapType(x) == ']':
        indentLevel -= len(x)
        if not silent:
            print(f'COMPILE: ] {len(x)}')


    compiled += '\n'+'\t'*(indentLevel-thisChange) + thisLine

with open(sys.argv[2], 'w') as f:
    f.write(compiled)
