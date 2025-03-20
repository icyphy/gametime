#include <stdint.h>
#include <unistd.h>
#include <stdio.h>

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



