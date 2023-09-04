#include <stdint.h>
#include "flexpret.h"

uint32_t add(uint32_t a, uint32_t b) {
    return a + b;
}

int main() {

    uint32_t x = 1;
    _fp_print(x);
    uint32_t y = 2;
    _fp_print(y);
    for (int i = 0; i < 5; i++){
        if (x < y + 10) {
            uint32_t z = add(x, y);
            _fp_print(z);
            x = z;
        }
    }

    return 0;
}
