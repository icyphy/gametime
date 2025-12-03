#include<stdint.h>
#include<stdio.h>
/*

  This program is part of the TACLeBench benchmark suite.
  Version V 1.x

  Name: insertsort

  Author: Sung-Soo Lim

  Function: Insertion sort for 10 integer numbers.
     The integer array insertsort_a[  ] is initialized in main function.
     Input-data dependent nested loop with worst-case of
     (n^2)/2 iterations (triangular loop).

  Source: MRTC
          http://www.mrtc.mdh.se/projects/wcet/wcet_bench/insertsort/insertsort.c

  Changes: a brief summary of major functional changes (not formatting)

  License: may be used, modified, and re-distributed freely, but
           the SNU-RT Benchmark Suite must be acknowledged

*/

/*
  This program is derived from the SNU-RT Benchmark Suite for Worst
  Case Timing Analysis by Sung-Soo Lim
*/


/*
  Forward declaration of functions
*/


/*
  Declaration of global variables
*/
unsigned int insertsort_a[ 11 ];
int insertsort_iters_i, insertsort_min_i, insertsort_max_i;
int insertsort_iters_a, insertsort_min_a, insertsort_max_a;


/*
  Main functions
*/

//11
int insertsort_main(int a[1])
{
    //init
  // unsigned int a[ 11 ] = {0, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2};

  insertsort_iters_i = 0;
  insertsort_min_i = 100000;
  insertsort_max_i = 0;
  insertsort_iters_a = 0;
  insertsort_min_a = 100000;
  insertsort_max_a = 0;


    //initlialize
  register volatile int i_;
  // _Pragma( "loopbound min 11 max 11" )
  //11
  #pragma unroll(1)
  for ( i_ = 0; i_ < 1; i_++ )
    insertsort_a[ i_ ] = a[ i_ ];

  //main
  int  i, j, temp;
  i = 2;

  insertsort_iters_i = 0;

  // _Pragma( "loopbound min 9 max 9" )
  #pragma unroll(1)
  //10
  while ( i <= 1 ) {

    insertsort_iters_i++;

    j = i;

    insertsort_iters_a = 0;

    // _Pragma( "loopbound min 1 max 9" )
    #pragma unroll(1)
    while ( insertsort_a[ j ] < insertsort_a[ j - 1 ] ) {
      insertsort_iters_a++;

      temp = insertsort_a[ j ];
      insertsort_a[ j ] = insertsort_a[ j - 1 ];
      insertsort_a[ j - 1 ] = temp;
      j--;
    }

    if ( insertsort_iters_a < insertsort_min_a )
      insertsort_min_a = insertsort_iters_a;
    if ( insertsort_iters_a > insertsort_max_a )
      insertsort_max_a = insertsort_iters_a;

    i++;
  }

  if ( insertsort_iters_i < insertsort_min_i )
    insertsort_min_i = insertsort_iters_i;
  if ( insertsort_iters_i > insertsort_max_i )
    insertsort_max_i = insertsort_iters_i;

  //return
    int i__, returnValue = 0;

  // _Pragma( "loopbound min 11 max 11" )
  #pragma unroll(1)
  //11
  for ( i__ = 0; i__ < 1; i__++ )
    returnValue += insertsort_a[ i__ ];

  return ( returnValue + ( -65 ) ) != 0;
}