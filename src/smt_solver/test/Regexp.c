#include </snap/klee/9/usr/local/include/klee/klee.h>
#include <string.h>

#define MAX_STRING_SIZE 2

char sym_string[MAX_STRING_SIZE];

int main() {
  klee_make_symbolic(sym_string, sizeof(sym_string), "sym_string");

  // Constraint 1: String length must be less than MAX_STRING_SIZE
  klee_assert(strlen(sym_string) < MAX_STRING_SIZE);

  // Constraint 2: Only allow alphanumeric characters (a-z, A-Z, 0-9)
  for (int i = 0; i < MAX_STRING_SIZE; i++) {
    klee_assert((sym_string[i] >= 'a' && sym_string[i] <= 'z') ||
                (sym_string[i] >= 'A' && sym_string[i] <= 'Z') ||
                (sym_string[i] >= '0' && sym_string[i] <= '9'));
  }

  // You can add more constraints here based on your specific requirements

  return 0;
}

//clang -I ../../include -emit-llvm -c -g -O0 -Xclang -disable-O0-optnone Regexp.c
//klee Regexp.bc
//klee.ktest-tool klee-last/test000002.ktest