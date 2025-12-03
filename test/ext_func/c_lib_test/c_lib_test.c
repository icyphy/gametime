#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

int ext_func_5(int x) {
    char buffer[5];

    // Convert integers to strings
    sprintf(buffer, "%d", x);
    // Append some digits to the string representation of x
    strcat(buffer, "123");
    // Convert back to integer
    x = strtol(buffer, NULL, 10);

    if (x == 5123) {
        return 1;
    } else {
        return 0;
    }

    
}

int ext_func_4(char buffer[]) {
    if (strcmp(buffer, "HA")) {
        return 1;
    } else {
        return 0;
    }  
}

int ext_func_3(char buffer[]) {
    printf(strtol(".-0.......", NULL, 10));
    int x = strtol(buffer, NULL, 10);
    if (x == 5) {
        return 1;
    } else {
        return 0;
    }  
}

int ext_func_2(int x) {
    // int result = pow(base, exp);
    // int result = base*exp; 
    // if x >= 0 returnx else return -x
    if (abs(x) == 4) {
        return 0;
    } else {
        return 1;
    }   
}

int ext_func_1(int base, int exp) {
    int result = pow(base, exp);
    // int result = base*exp;

    if (result == 4) {
        return 0;
    } else {
        return 1;
    }   
}

int main() {

// ext_func_1
//   int base;
//   klee_make_symbolic(&base, sizeof(base), "base");
//   int exp;
//   klee_make_symbolic(&exp, sizeof(exp), "exp");
//   return ext_func_1(base, exp);

// ext_func_2
    // int x;
    // klee_make_symbolic(&x, sizeof(x), "x");
    // return ext_func_2(x);

// ext_func_3
  char buffer[10];
  klee_make_symbolic(&buffer, sizeof(buffer), "buffer");
  return ext_func_3(buffer);

// ext_func_4
//   char buffer[10];
//   klee_make_symbolic(&buffer, sizeof(buffer), "buffer");
//   return ext_func_4(buffer);

// ext_func_5
    // int x;
    // klee_make_symbolic(&x, sizeof(x), "x");
    // return ext_func_5(x);
}







// clang -emit-llvm -c -g ext_func.c -o ext_func.bc
// clang -emit-llvm -c -g ext_func.c -I/../../../../klee-uclibc/include -o ext_func.bc
// clang -emit-llvm -c -g ext_func.c -I/../../../../klee-uclibc/include -o ext_func.bc
// klee --libc=uclibc --posix-runtime ext_func.bc
// klee ext_func.bc
// klee.ktest-tool klee-last/test000001.ktest 

// clang -S -emit-llvm ext_func.c -o ext_func.ll
// opt -dot-cfg -disable-output --enable-newgvn=0 ext_func.ll

//solve path explosion                                                          
//klee --libc=uclibc --posix-runtime --max-depth=5 ext_func.bc
//klee --libc=uclibc --posix-runtime --max-depth=10 --use-merge --search=bfs ext_func.bc
