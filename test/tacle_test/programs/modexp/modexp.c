#include <unistd.h>
#include <stdint.h>

int modexp(uint8_t base, uint8_t exponent) {
    uint8_t p = 255;
    uint8_t result = 1;
    #pragma unroll 8
    for(int i=8; i>0; i--) { 
        if ((exponent & 1) == 1) { 
            result = (result * base) % p;
        }
        exponent >>= 1;
        base = (base * base) % p;
    }
    return result; 
    // uint8_t p = 255;
    // uint8_t result = 1;
    // if ((exponent & 1) == 1) {
    //     result = (result * base) % p;
    // }
    // exponent >>= 1;
    // base = (base * base) % p;
    // if ((exponent & 1) == 1) {
    //     result = (result * base) % p;
    // }
    // exponent >>= 1;
    // base = (base * base) % p;
    // if ((exponent & 1) == 1) {
    //     result = (result * base) % p;
    // }
    // exponent >>= 1;
    // base = (base * base) % p;
    // if ((exponent & 1) == 1) {
    //     result = (result * base) % p;
    // }
    // exponent >>= 1;
    // base = (base * base) % p;
    // if ((exponent & 1) == 1) {
    //     result = (result * base) % p;
    // }
    // exponent >>= 1;
    // base = (base * base) % p;
    // if ((exponent & 1) == 1) {
    //     result = (result * base) % p;
    // }
    // exponent >>= 1;
    // base = (base * base) % p;
    // if ((exponent & 1) == 1) {
    //     result = (result * base) % p;
    // }
    // exponent >>= 1;
    // base = (base * base) % p;
    // if ((exponent & 1) == 1) {
    //     result = (result * base) % p;
    // }

    // exponent >>= 1;
    // base = (base * base) % p;
    
    // return result;
}