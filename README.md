# bfasm
weird brainfuck assembly language compiler(?) and stdlib

### Tested on ubuntu 20.04 LTS and python 3.8.10

## file extensions
  `.bf` - raw brainfuck file, runnable in other brainfuck interpreters
  
  `.bfpy` - brainfuck compiled into python code, runs in python
  
  `.bfasm` - whole repo centers around this, it's a language loosely based on assembly (very loosely)

## bfasm syntax
- Functions
  - `.function %arg1 %arg2 ... %argN` -> takes a set amount of arguments when called
  - `-function %arg1 %arg2 ... %argN` -> arguments given when called must be divisible by number of arguments
- Calling functions
  - `.function $number "string" @memory_address` -> enters function and passes args, throws error if not same number of args passed in as accepted in declaration
  - `-function $number "string" @memory_address` -> enters function len(function args) / len(call args), throws error if not whole number of enters
- Examples
```
; this program prints 'a'
; it can be run by going into this repo's directory on your machine and then running ./runasm pathToProg.bfasm someInputFile.txt
; if that fails, it might be because the ./runasm binary is not compiled for your machine
; if you are unable to compile runasm.c for your machine you can call each python file that runasm.c calls on your own
; the commands it executes are:

; $ python3 assemble.py pathToThisProg.bfasm run.bf
; $ python3 compileToPython.py run.bf run.bfpy
; $ python3 run.bfpy someInputFile.txt

#include stdlib/stdio.bfasm
; during preprocessing append the stdio module in the stdlib to the end of this program

.start
  ; this function is entered by the compiler(?)
  
  alloc @a
  ; allocate a cell in the bf memory and let it be referenced in this program by the name '@a'
  
  > @a {+} * "a"
  ; code injection, goes to the memory cell @a and injects '+' * 97
  
  free @a
  ; makes the memory cell located at @a free to be reallocated, does not reset the cell
```
```
; this program prints fibbonacci numbers as ascii chars
; follow instructions on how to run the above program

; ===this program is not tested===

#include stdlib/stdio.bfasm
#include stdlib/stdv.bfasm

.start
  alloc @a @b @c
  .set @a $0
  .set @a $1
  > {[}
  .setv @c @a
  .addv @c @b
  -printv @a
  .setv @a @b
  .setv @b @c
  > {]}}
```
