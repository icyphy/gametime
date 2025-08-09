#include <flexpret/flexpret.h> 
#include <stdint.h>
#include <unistd.h>
#include <stdio.h>

int abs(int x);

int test(int x){
    if (abs(x) == 4) {
        return 0;
    } else {
        int a = 1;
        int b = a * 2;
        int c = a * b;
        return c;
    }
}




static inline unsigned long read_cycle_count() {
    return rdcycle();
}
int x = 0x00000000
;int main(int argc, char ** argv)
{
  unsigned long long start;
  unsigned long long end;
  start = read_cycle_count();
  test(x);
  end = read_cycle_count();
  printf("%i\n", (uint32_t) (end - start));
  return 0;
}

