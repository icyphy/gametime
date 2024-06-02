#include <stdint.h>
#include </snap/klee/9/usr/local/include/klee/klee.h>
int test (int x, int b) {
   if (x < 0 && b < 0) {
      return 1;
   } else {
      return 9;
   }
}

int main() {
    int x;
    int* b;

    klee_make_symbolic(&x, sizeof(x), "x");
    klee_make_symbolic(&b, sizeof(b), "b");
    klee_assert(test(x, *b) == 1);
}

//clang -I ../../include -emit-llvm -c -g -O0 -Xclang -disable-O0-optnone check_pointer2.c
//klee check_pointer2.bc
//klee.ktest-tool klee-last/test000010.ktest