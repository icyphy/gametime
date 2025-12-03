#include <stdint.h>
#include <unistd.h>
#include <stdio.h>

int abs(int x);

int test(int x){
    if (x == 4) {
        int a = 1;
        int b = a * 2;
        int c = a * b;
    }
    if (x == 4) {
        int a = 1;
        int b = a * 2;
        int c = a * b;
        return c;
    }
    return 0;
}



