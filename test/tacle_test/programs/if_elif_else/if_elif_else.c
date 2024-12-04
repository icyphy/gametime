#include <stdint.h>
#include <unistd.h>
#include <stdio.h>

int abs(int x);

int test(int x){
    if (abs(x) == 4) {
        return 0;
    } else {
        return 1;
    }
}



