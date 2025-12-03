/*

  This program is part of the TACLeBench benchmark suite.
  Version 2.0

  Name: bsort

  Author: unknown

  Function: A program for testing the basic loop constructs,
            integer comparisons, and simple array handling by
            sorting 100 integers

  Source: MRTC
          http://www.mrtc.mdh.se/projects/wcet/wcet_bench/bsort100/bsort100.c

  Original name: bsort100

  Changes: See ChangeLog.txt

  License: May be used, modified, and re-distributed freely.

*/



/*
  Declaration of global variables
*/

#define bsort_SIZE 3




int bsort_return( int Array[]  )
{
  int Sorted = 1;
  int Index;

  #pragma unroll 3
  for ( Index = 0; Index < bsort_SIZE - 1; Index ++ )
    Sorted = Sorted && ( Array[ Index ] < Array[ Index + 1 ] );

  return 1 - Sorted;
}


/*
  Core benchmark functions
*/

/* Sorts an array of integers of size bsort_SIZE in ascending
   order with bubble sort. */
int bsort_BubbleSort( int Array[] )
{
  int Sorted = 0;
  int Temp, Index, i;

  #pragma unroll 3
  for ( i = 0; i < bsort_SIZE - 1; i ++ ) {
    Sorted = 1;
    #pragma unroll 3
    for ( Index = 0; Index < bsort_SIZE - 1; Index ++ ) {
      if ( Index > bsort_SIZE - i )
        break;
      if ( Array[ Index ] > Array[Index + 1] ) {
        Temp = Array[ Index ];
        Array[ Index ] = Array[ Index + 1 ];
        Array[ Index + 1 ] = Temp;
        Sorted = 0;
      }
    }

    if ( Sorted )
      break;
  }
  int res = bsort_return(Array);
  return res;
}

