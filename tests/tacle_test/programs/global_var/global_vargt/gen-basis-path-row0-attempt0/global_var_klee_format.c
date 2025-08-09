#include <klee/klee.h>
#include <stdbool.h>


bool conditional_var_0 = false;
bool conditional_var_1 = false;
bool conditional_var_2 = false;

int g;  

int test() {
    int result = 0;

    if (g == 10) {
        result = g * 2 + 5 - 3;  
    } 
    return result;
}
int main() {
    test();
    klee_assert(conditional_var_0);
    klee_assert(conditional_var_1);
    klee_assert(conditional_var_2);
    return 0;
}