#---------------------------------------------------------------------------
# Makefile for ARM processor on Portux920T embedded board
#---------------------------------------------------------------------------

# Main target output filename
PRG= wvr

#---------------------------------------------------------------------------
# Toolchain and flags
#---------------------------------------------------------------------------
# Add svn revision to code
SVNREV= PART_SVN='"$(shell svnversion -n .)"'

# Compiler and linker flags
CFLAGS= -D$(SVNREV) -O2 -Wall -g

CC= gcc
OBJCOPY= objcopy
OBJDUMP= objdump
STRIP= strip

#---------------------------------------------------------------------------
# Compiler work scheme
#---------------------------------------------------------------------------

all: $(PRG)

$(PRG): main.o Makefile
	$(CC) $(LDFLAGS) -o $(PRG) main.o
	$(STRIP) $(PRG)

main.o: main.c Makefile
	$(CC) $(CFLAGS) -c main.c -o main.o

clean:
	rm -f $(PRG)
	rm -f *.o

.PHONY: all clean
