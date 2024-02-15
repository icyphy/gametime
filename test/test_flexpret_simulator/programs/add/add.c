// #include <stdint.h>
// #include "flexpret.h"

// uint32_t add(uint32_t a, uint32_t b) {
//     return a + b;
// }

// int main() {
    
//     uint32_t x = 1;
//     // _fp_print(x);
//     uint32_t y = 2;
//     // _fp_print(y);

//     uint32_t z = add(x, y);
//     // _fp_print(z);

//     // assert(z == 3);
//     return 0;
// }
#include <stdint.h>
#include "flexpret.h"

uint32_t add(uint32_t a, uint32_t b) {
    return a + b;
}

int main() {
    
    uint32_t x = 1;
    // printf("x is %i\n", x);
    uint32_t y = 2;
    // printf("y is %i\n", y);

    uint32_t z = add(x, y);
    // printf("z is %i\n", z);
    // assert(z == 3, "1 + 2 =/= 3");
    return 0;
}

