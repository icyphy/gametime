#include <unistd.h>
#include <stdint.h>

int modexp(uint8_t base, uint8_t exponent) {
    uint8_t p = 255;
    uint8_t result = 1;
    uint8_t number_of_one = 0;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
        number_of_one += 1;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
        number_of_one += 1;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
        number_of_one += 1;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
        number_of_one += 1;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
        number_of_one += 1;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
        number_of_one += 1;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
        number_of_one += 1;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
        number_of_one += 1;
    }
    // if (number_of_one == 8) {
    //     usleep(1000);
    // }
    exponent >>= 1;
    base = (base * base) % p;
    
    return result;
}