/*

  This program is part of the TACLeBench benchmark suite.
  Version V 1.9

  Name: deg2rad

  Author: unknown

  Function: deg2rad performs conversion of degree to radiant

  Source: MiBench
          http://wwweb.eecs.umich.edu/mibench

  Original name: basicmath_small

  Changes: no major functional changes

  License: this code is FREE with no restrictions

*/

#define PI 3.14f

#define deg2rad(d) ((d)*PI/180)


/*
  Main functions
*/

int  deg2rad_main( float deg2rad_X, float deg2rad_Y )
{
  /* convert some rads to degrees */
  #pragma unroll 10
  for ( deg2rad_X = 0.0f; deg2rad_X <= 360.0f; deg2rad_X += 1.0f )
    deg2rad_Y += deg2rad( deg2rad_X );
  
  if ( deg2rad_Y == 1133 )
    return 0;
  else
    return -1;
}