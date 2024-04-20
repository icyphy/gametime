//TACLE kernel/prime/prime.c

/*
  Forward declaration of functions
*/



int prime_prime ( int n )
{
  unsigned int i = 3;
  if ( n % 2 )
    return ( n == 2 );
  // _Pragma( "loopbound min 0 max 16" )  
  #pragma unroll 16
  for ( i = 3; i * i <= 357; i += 2 ) {
    if ( n % i ) /* ai: loop here min 0 max 357 end; */
      return 0;
  }

}