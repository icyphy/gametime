/*
  Adapted from TACLe kernel binarysearch
*/

int binarysearch_binary_search(int binarysearch_data [15], int x )
{
  int fvalue, mid, up, low;

  low = 0;
  up = 14;
  fvalue = -1;

  _Pragma( "loopbound min 1 max 4" )
  while ( low <= up ) {
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

  return ( fvalue );
}

