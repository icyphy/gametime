#include <stdint.h>
#include <stdbool.h>
#include <unistd.h>
#include <stdio.h>

int abs(int x);

// int test (int x) {
//    // if (x < 0 && b < 0) {
//    //    // sleep(5);
//    //    return 1;
//    // } else if (x < 0 && b == 0) {
//    //    return 2;
//    // } else if (x < 0 && b > 0) {
//    //    return 3;
//    // } else if (x == 0 && b < 0) {
//    //    return 4;
//    // // } else if (x == 0 && b == 0) {
//    // //    return 5;
//    // // } else if (x == 0 && b > 0) {
//    // //    return 6;
//    // // } else if (x > 0 && b < 0) {
//    // //    return 7;
//    // // } else if (x > 0 && b == 0) {
//    // //    return 8;
//    // } else {
//    //    return 9;
//    // }
//    if(x > 0) {
//       return 1;
//    } else {
//       return 0;
//    }
// }

// int abs(int x) {
//     return x >= 0 ? x : -x;
// }

int test(int x){
    if (abs(x) == 4) {
        return 0;
    } else {
        return 1;
    }
}



