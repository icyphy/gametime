//TACLE kernel/prime/prime.c

/*
  Forward declaration of functions
*/

#include<stdio.h>
#include <unistd.h>
#include <stdint.h>

int prime_prime ( int n )
{
  unsigned int i = 3;
  if ( n % 2 )
    return ( n == 2 );
  // _Pragma( "loopbound min 0 max 16" )  
  #pragma unroll 5
  // #pragma clang loop unroll(full)
  for ( i = 3; i * i <= 3; i += 2 ) {
    if ( n % i ) /* ai: loop here min 0 max 357 end; */
      return 0;
    // n+=1;
  }

  return n;

}


