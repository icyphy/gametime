#include </opt/homebrew/include/klee/klee.h>
#include <stdbool.h>

#include <unistd.h>
#include <stdint.h>

bool conditional_var_0 = false;
bool conditional_var_1 = false;
bool conditional_var_2 = false;
bool conditional_var_3 = false;
bool conditional_var_4 = false;
bool conditional_var_5 = false;
bool conditional_var_6 = false;
bool conditional_var_7 = false;
bool conditional_var_8 = true;
bool conditional_var_9 = true;
bool conditional_var_10 = true;
bool conditional_var_11 = true;
bool conditional_var_12 = true;
bool conditional_var_13 = true;
bool conditional_var_14 = true;
bool conditional_var_15 = true;
bool conditional_var_16 = true;
bool conditional_var_17 = true;
bool conditional_var_18 = true;
bool conditional_var_19 = true;
bool conditional_var_20 = true;
bool conditional_var_21 = true;
bool conditional_var_22 = true;
bool conditional_var_23 = true;
bool conditional_var_24 = true;
bool conditional_var_25 = true;
bool conditional_var_26 = true;
bool conditional_var_27 = true;
bool conditional_var_28 = true;
bool conditional_var_29 = true;
bool conditional_var_30 = true;
bool conditional_var_31 = true;
bool conditional_var_32 = true;
bool conditional_var_33 = true;
bool conditional_var_34 = true;
bool conditional_var_35 = true;
bool conditional_var_36 = true;
bool conditional_var_37 = true;

/*
  Adapted from TACLe kernel binarysearch
*/



int binarysearch_binary_search(int x )
{
  int fvalue, mid, up, low;

  low = 0;
  up = 14;
  fvalue = -1;
  int binarysearch_data[15] = {0,1,2,3,4,5,6,7,8,9,10,11,12,13,14};

  // #pragma unroll 4
  // for (int i = 0; i < 4; i++) {
  //   if (low <= up) {
  //     mid = ( low + up ) >> 1;
    
  //     if ( binarysearch_data[ mid ] == x ) {
  //       /* Item found */
  //       up = low - 1;
  //       fvalue = binarysearch_data[ mid ];
  //     } else {
  //         if ( binarysearch_data[ mid ] > x )
  //           /* Item not found */
  //           up = mid - 1;
  //         else
  //           low = mid + 1;
  //     }
  //   }
  
  // }
  #pragma unroll 5
  while (low <= up) {
    mid = ( low + up ) >> 1;
    
    if ( binarysearch_data[ mid ] == x ) {
      /* Item found */
      up = low - 1;
      fvalue = binarysearch_data[ mid ];
    } else {
        if ( binarysearch_data[ mid ] > x )
            /* Item not found */
            up = mid - 1;
        else
            low = mid + 1;
    }
  }

  return fvalue;
}


int main() {
    int x;
    klee_make_symbolic(&x, sizeof(x), "x");
    binarysearch_binary_search(x);
    klee_assume(conditional_var_0);
    klee_assume(conditional_var_1);
    klee_assume(conditional_var_2);
    klee_assume(conditional_var_3);
    klee_assume(conditional_var_4);
    klee_assume(conditional_var_5);
    klee_assume(conditional_var_6);
    klee_assume(conditional_var_7);
    klee_assume(conditional_var_8);
    klee_assume(conditional_var_9);
    klee_assume(conditional_var_10);
    klee_assume(conditional_var_11);
    klee_assume(conditional_var_12);
    klee_assume(conditional_var_13);
    klee_assume(conditional_var_14);
    klee_assume(conditional_var_15);
    klee_assume(conditional_var_16);
    klee_assume(conditional_var_17);
    klee_assume(conditional_var_18);
    klee_assume(conditional_var_19);
    klee_assume(conditional_var_20);
    klee_assume(conditional_var_21);
    klee_assume(conditional_var_22);
    klee_assume(conditional_var_23);
    klee_assume(conditional_var_24);
    klee_assume(conditional_var_25);
    klee_assume(conditional_var_26);
    klee_assume(conditional_var_27);
    klee_assume(conditional_var_28);
    klee_assume(conditional_var_29);
    klee_assume(conditional_var_30);
    klee_assume(conditional_var_31);
    klee_assume(conditional_var_32);
    klee_assume(conditional_var_33);
    klee_assume(conditional_var_34);
    klee_assume(conditional_var_35);
    klee_assume(conditional_var_36);
    klee_assume(conditional_var_37);
    return 0;
}