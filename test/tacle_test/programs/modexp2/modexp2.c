#include <unistd.h>
#include <stdint.h>
#include <stdio.h>
void check_base(int base) {
    uint8_t p = 255;
    uint8_t result = 1;
    #pragma unroll 3
    for(int i=3; i>0; i--) { 
        if ((base & 1) == 1) { 
            result = (result * base) % p;
        }
        base >>= 1;
        base = (base * base) % p;
    }
}
int modexp(uint8_t base, uint8_t exponent) {
    uint8_t p = 255;
    uint8_t result = 1;
    check_base(base);
    #pragma unroll 3
    for(int i=3; i>0; i--) { 
        if ((exponent & 1) == 1) { 
            result = (result * base) % p;
        }
        exponent >>= 1;
        base = (base * base) % p;
    }
    return result; 
}