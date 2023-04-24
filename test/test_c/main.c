//
// Created by AZ on 10/9/2022.
//

#include "main.h"
#include <stdio.h>

int foo(int j) {
//  #pragma clang loop unroll_count(10)
//  for (int i = 0; i < 10; i++) {
//    // printf("%d \n", j);
//    j+=i;
//    j %= (2*i);
//  }
  j = j+1;
  return j;
}

int main(int argc, char *argv[]) {
  int j = 0;

  j = foo(j);

//  if (j > argc) {
//    j = (j + 100) % 33;
//  }
  return j;
  // printf("%d\n", j);
}

