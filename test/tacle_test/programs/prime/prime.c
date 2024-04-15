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
  #pragma unroll 1
  for ( i = 3; i * i <= n; i += 2 ) {
    if ( n % i ) /* ai: loop here min 0 max 357 end; */
      return 0;
  }

  // if ( n % i )
  //   return 0;
  // i += 2;

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }  

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }  

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }  

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // } 

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }  

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }

  // if (i * i <= n) {
  //   if ( n % i )
  //     return 0;
  //   i += 2;
  // } else {
  //   return ( n > 1 );
  // }      
}