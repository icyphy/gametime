#include <flexpret/flexpret.h> 
int g;  

int test() {
    int result = 0;

    if (g == 10) {
        result = g * 2 + 5 - 3;  
    } 
    return result;
}int g;

static inline unsigned long read_cycle_count() {
    return rdcycle();
}
int main(int argc, char ** argv)
{
  unsigned long long start;
  unsigned long long end;
  start = read_cycle_count();
  test();
  end = read_cycle_count();
  printf("%i\n", (uint32_t) (end - start));
  return 0;
}

