#include <flexpret/flexpret.h> 
/*
  Adapted from TACLe kernel binarysearch
*/
#include <unistd.h>
#include <stdint.h>

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


static inline unsigned long read_cycle_count() {
    return rdcycle();
}
int x = 0x0000000c
;int main(int argc, char ** argv)
{
  unsigned long long start;
  unsigned long long end;
  start = read_cycle_count();
  binarysearch_binary_search(x);
  end = read_cycle_count();
  printf("%i\n", (uint32_t) (end - start));
  return 0;
}

