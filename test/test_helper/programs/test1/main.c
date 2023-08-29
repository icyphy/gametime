//
// Created by AZ on 10/9/2022.
//
#include <stdio.h>

int main() {
  int j = 0;

  for (int i = 0; i < 10; i++) {
    j+=i;
    j %= (2*i);
  }

  return j;
}
