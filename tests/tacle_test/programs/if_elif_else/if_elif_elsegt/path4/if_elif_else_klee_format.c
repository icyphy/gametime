#include </opt/homebrew/include/klee/klee.h>
#include <stdbool.h>

#include <stdint.h>
#include <unistd.h>
#include <stdio.h>

bool conditional_var_0 = false;
bool conditional_var_1 = false;
bool conditional_var_2 = false;
bool conditional_var_3 = false;
bool conditional_var_4 = true;
bool conditional_var_5 = true;

int abs(int x);

int test(int x){
    if (abs(x) == 4) {
        return 0;
    } else {
        int a = 1;
        int b = a * 2;
        int c = a * b;
        return c;
    }
}




int main() {
    int x;
    klee_make_symbolic(&x, sizeof(x), "x");
    test(x);
    klee_assume(conditional_var_0);
    klee_assume(conditional_var_1);
    klee_assume(conditional_var_2);
    klee_assume(conditional_var_3);
    klee_assume(conditional_var_4);
    klee_assume(conditional_var_5);
    return 0;
}