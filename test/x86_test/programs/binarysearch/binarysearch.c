/*
  Adapted from TACLe kernel binarysearch
*/
#include <unistd.h>
#include <stdint.h>

int binarysearch_binary_search(uint8_t binarysearch_data [15], uint8_t x )
{
  uint8_t fvalue, mid, up, low;

  low = 0;
  up = 14;
  fvalue = -1;

  #pragma unroll 4
  for (int i = 0; i < 4; i++) {
    if (low <= up) {
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
  
  }
  // while (low <= up) {
  //   mid = ( low + up ) >> 1;
    
  //   if ( binarysearch_data[ mid ] == x ) {
  //     /* Item found */
  //     up = low - 1;
  //     fvalue = binarysearch_data[ mid ];
  //   } else {
  //       if ( binarysearch_data[ mid ] > x )
  //           /* Item not found */
  //           up = mid - 1;
  //       else
  //           low = mid + 1;
  //   }
  // }

  return fvalue;
}

