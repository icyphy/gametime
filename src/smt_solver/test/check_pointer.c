#include </snap/klee/9/usr/local/include/klee/klee.h>
#include <stdio.h>

#define ARRAY_SIZE 5

int data_array[ARRAY_SIZE] = {1, 2, 3, 4, 5};

int main() {
    int* sym_ptr;
    // Symbolic pointer
    klee_make_symbolic(&sym_ptr, sizeof(sym_ptr), "sym_ptr");

    // Constraint 1: Pointer points within the data array bounds
    klee_assert(sym_ptr >= data_array && sym_ptr < data_array + ARRAY_SIZE);

    // Attempt 1: Manual Check (Limited Effectiveness)
    // This approach has limitations (see explanation)
  
    klee_assert(*(sym_ptr) > 0);  // Check if dereferenced value is positive

    // You can add more constraints based on your specific requirements

    return 0;
}

//clang -I ../../include -emit-llvm -c -g -O0 -Xclang -disable-O0-optnone check_pointer.c
//klee check_pointer.bc
//klee.ktest-tool klee-last/test000003.ktest