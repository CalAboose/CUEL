CUEL Manual
===========================
---------------------------
&nbsp;  
##Content##
**1. Overview**  
**2. Programmer's Manual**  
>**2.1. Compilation**  
>**2.2. Execution**  
>**2.3. Program structure**  
>**2.4. Program operation**  
>**2.5. Built-in functions**  
>**2.6. Example program**  

**3. Developer's Manual**  
>**3.1. Instruction set**  
>**3.2. Bytecode file format**  
>**3.3. Program execution**  
  
**Appendix A - EBNF**  

&nbsp;  
&nbsp;  
  
1. Overview
---------------------

CUEL is a stack-based concatenative programming language. 
A program written in it consists of function definitions, only.
Every function definition represents a sequence of function calls.
It has built-in functions for arithmetic operations, branching,
stack manipulation and basic I/O work. Functions take their arguments
from the data stack and push the result back to the stack. Recursion is 
utilized for repetitive tasks.

&nbsp;  
&nbsp;  
  
2. Programmer's Manual
----------------------

A CUEL program compiles to bytecode which is then executed by a
virtual machine. The whole program consists of a single source code file.
CUEL has a rather strict syntax. The EBNF can be found in Appendix A.

&nbsp;  

###2.1. Compilation###
  
The compiler is written in Python and is named 'cuelc'.
Compilation takes as input a CUEL source file and produces a file 
containing the program's executable bytecode.
The source files' file extension is 'cuel'.
For compilation the following is typed in a console:

`$ python cuelc.py FILE`

Where FILE is the path to the program's source code.

&nbsp;  

###2.2. Execution###
  
The virtual machine is written in Python and is named 'cuelvm'.
It executes files containing CUEL bytecode.
Bytecode files' file extension is 'cuby'.
To run a program requires the following to be typed in a console:

`$ python cuelvm.py FILE`

Where FILE is the path to the program's bytecode.

&nbsp;  

###2.3. Program structure###

A CUEL source file contains a sequence of function definitions 
separated by a blank line. Every definition starts with the function's name
immediately followed by a colon and a new line. The function's body follows
after the function's name and consists of consecutive lines of function calls.
Every line represents exactly one function call. The first function definition
is always that of the main function. It is called 'MAIN' and program execution
starts from it. Command-line arguments are not supported.

&nbsp;  

###2.4. Program operation###

Every program statement occupies a separate line and is a call to a built-in 
function or a user defined function in the program's source file. Program execution 
requires the use of two stacks - call stack and data stack. The call stack stores 
the user defined functions' return address on invocation. The data stack 
stores the program's data. Function calls pop their arguments from 
the data stack and push the result back to it. The data stack is cyclic
which allows access to every value on the stack, not just the top.

&nbsp;  

###2.5. Built-in functions###

All arithmetic operations work with integer values.

*TOP* refers to the top of the data stack.  
*TOP-1* refers to the value immediately below *TOP*.  
*TOP-2* refers to the value immediately below *TOP-1*.  
*BOTTOM* refers to the bottom of the data stack.  

**cal &lt;FUNC-NAME&gt;** - calls the user defined function named &lt;FUNC-NAME&gt;.  
**caz &lt;FUNC-NAME&gt;** - calls the user defined function named &lt;FUNC-NAME&gt; if *TOP* is zero.  
**cnz &lt;FUNC-NAME&gt;** - calls the user defined function named &lt;FUNC-NAME&gt; if *TOP* is not zero.  
**cgz &lt;FUNC-NAME&gt;** - calls the user defined function named &lt;FUNC-NAME&gt; if *TOP* is greater than zero.  
**clz &lt;FUNC-NAME&gt;** - calls the user defined function named &lt;FUNC-NAME&gt; if *TOP* is less than zero.  

**swp** - swaps *TOP* and *TOP-1*.  
**swx** - swaps *TOP* and *TOP-2*.  
**rcw** - rotate data stack clockwise. Effectively pops *TOP* and makes it the new *BOTTOM*.  
**rcc** - rotate data stack counterclockwise. Effectively pops *BOTTOM* and makes it the new *TOP*.  

**pop** - pops *TOP*.  
**dup** - duplicates *TOP*.  

**neg** - negates *TOP*.  
__+__ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- sums *TOP-1* with *TOP*.  
__&#42;__ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- multiplies *TOP-1* by *TOP*.  
__/__ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- divides *TOP-1* by *TOP*.  
__-__ &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;- subtracts *TOP* from *TOP-1*.  
__%__ &nbsp;&nbsp;&nbsp;&nbsp;- modulo *TOP-1* by *TOP*.  

**getn** - reads a number from standard input and pushes it on the data stack.  
**putn** - pops *TOP* and writes it to the standard output.  
**puts** - pops a string off the data stack and writes it to standard output.  

**&lt;number&gt;** - pushes a positive integer with value &lt;number&gt; on the data stack.  
**&lt;string&gt;** - pushes a zero terminated sequence of positive integer values
on the data stack. The values represent ASCII characters.

&nbsp;  

###2.6. Example program###

A program for computing the factorial of a number entered by the user:

	MAIN:
	       "Enter number: "  
	       puts  
	       1  
	       getn  
	       dup  
	       cgz FACT  
	       pop  
	       putn  

	FACT:
	       dup  
	       swx  
	       *  
	       swp  
	       1  
	       -  
	       dup  
	       cgz FACT  

&nbsp;  
&nbsp;  

3. Developer's Manual
----------------------

&nbsp;  

###3.1. Instruction set###

The program's source code compiles to virtual machine instructions.
Every built-in function has a corresponding machine instruction.
There's an additional instruction called 'ret' that returns from a function call.
It is inserted in the bytecode after every function's body automatically by the compiler.
Numbers are instructions as well. Every number represents a unique instruction.
Strings are inserted in the bytecode as zero terminated sequence of numbers.

&nbsp;  

###3.2. Bytecode file format###

Every machine instruction is encoded as a 32-bit signed value. The whole 
bytecode file is a sequence of 32-bit instructions. The only exception is 
the first value which is the magic number - 0x4C455543.
For the actual encoding of the instruction set refer to the source code.

&nbsp;  

###3.3. Program execution###

Upon execution the VM loads the bytecode in memory and begins executing the instruction
sequence starting from index 1 - the first instruction of the MAIN function. Execution 
continues until MAIN returns (via the 'ret' instruction). When a user defined function is called
the current value of the instruction pointer is pushed onto the call stack. Every function 
consists of a sequence of instructions and the last one is always 'ret'. When it is executed
the function's return address is popped from the call stack and assigned to the instruction pointer.
The function returns and execution continues in the caller.
Numbers are encoded as their 32-bit value. Only positive numbers can be encoded in the bytecode
since negative values represent the built-in functions. Thus number values are constrained
in the range of [0..2^31).
If an error occurs during execution the program terminates.

&nbsp;  
&nbsp;  

Appendix A - EBNF
----------------------


	program = main-function , eol , { { function , eol } , function } ;


	main-function = main-function-sig , eol , function-body ;

	main-function-sig = main-function-name , ":" ;

	main-function-name = "MAIN" ;


	function = function-sig , eol , function-body ;

	function-sig= function-name , ":" ;

	function-name = capletter , { { capletter | digit | "-" } , capletter | digit } ;


	function-body = function-body-line , { function-body-line } ;

	function-body-line = line-pad , function-call , eol ;


	func-call-name = main-function-name | function-name ;

	function-call = number | string |  
	                "cal" , white-space , func-call-name |  
	                "caz" , white-space , func-call-name |  
	                "cnz" , white-space , func-call-name |  
	                "cgz" , white-space , func-call-name |  
	                "clz" , white-space , func-call-name |  
	                "swp" | "swx" | "rcw" | "rcc" |  
	                "dup" | "pop" |  
	                "neg" | "+" | "*" | "/" | "-" | "%" |  
	                "getn" | "putn" | "puts" ;


	string = """ , { printable-ascii-char } , """ ;

	number = digit , { digit };


	digit = "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9" | "0" ;

	capletter = "A" | "B" | "C" | "D" | "E" | "F" | "G" | "H" | "I" | "J" | "K" | "L" | "M" |  
	            "N" | "O" | "P" | "Q" | "R" | "S" | "T" | "U" | "V" | "W" | "X" | "Y" | "Z" ;
	
	printable-ascii-char = ? what it says ? ;


	line-pad = 8 * white-space ;

	white-space = " " ;

	eol = ? new line ? ;