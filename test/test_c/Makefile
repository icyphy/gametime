CC=clang
CFLAGS=-emit-llvm
OPT=opt -dot-cfg

#%.bc: %.c
#	$(CC) -c $(CFLAGS) $@ -o $<
#
#main: main.bc
#	$(CC)

main.bc: main.c
	clang -emit-llvm -o main.bc -c main.c

main: main.bc
	clang -o main main.bc

.main.dot: main.bc
	opt -dot-cfg -S main.bc -disable-output -enable-new-pm=0

main.png: .main.dot
	dot -Tpng .main.dot -o main.png
