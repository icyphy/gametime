#include <stdlib.h>
#include <stdint.h>
#include "flexpret.h"

int main() {
    // Allocate an array
    int length = 10;
    uint32_t *arr = calloc(length, sizeof(uint32_t));
    #pragma unroll_completely
    for (uint32_t i = 0; i < length; i++) {
        arr[i] = i;
    }
    #pragma unroll_completely
    for (uint32_t j = 0; j < length; j++) {
        _fp_print(arr[j]);
//        assert(arr[j] == j);
    }

    // Free the memory.
    free(arr);

    return 0;
}