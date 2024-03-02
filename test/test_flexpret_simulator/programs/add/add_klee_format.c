#include </snap/klee/9/usr/local/include/klee/klee.h>
#include <stdbool.h>

#include <stdint.h>

bool conditional_var_0 = false;

// #include "flexpret.h"

// global A, B = 1, 2

uint32_t add(uint32_t a, uint32_t b) {
    return a + b;
}

// int main() {
    
//     uint32_t x = 1;
//     printf("x is %i\n", x);
//     uint32_t y = 2;
//     printf("y is %i\n", y);

//     uint32_t z = add(x, y);
//     printf("z is %i\n", z);
//     // assert(z == 3, "1 + 2 =/= 3");
//     //gpio pin set
//     // add(A, B);
//     //gpio pin set
//     return 0;
// }

// input program -> inline -> internal representation via clang -> CFG -> paths -> klee generated inputs -> get number on that input (use original program with runner) 
//  IN THE GAMETIME RUNNER ON HOST   //write parser to parse result file CSV

int main() {
    uint32_t a;
    klee_make_symbolic(&a, sizeof(a), "a");
    uint32_t b;
    klee_make_symbolic(&b, sizeof(b), "b");
    add(a, b);
    klee_assert(conditional_var_0);
    return 0;
}