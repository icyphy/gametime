#include </opt/homebrew/Cellar/klee/3.0_2/include/klee/klee.h>
#include <stdbool.h>

int get_sign(int x, bool b) {
   
   if (x < 0 && b) {
      return 1;
   } else if (x < 0 && !b) {
      return 2;
   } else if (x == 0 && b) {
      return 3;
   } else if (x == 0 && !b) {
      return 4;
   } else if (x > 0 && b) {
      return 5;
   } else {
      return 6;
   }
     
} 
