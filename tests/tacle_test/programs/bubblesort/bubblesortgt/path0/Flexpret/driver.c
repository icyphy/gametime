#include <flexpret/flexpret.h> 
void bubble_sort(int a0, int a1) {
    int temp;
    int arr[2] = {a0, a1};
    int i = 0;
    int j = 0;

    #pragma unroll 4
    while (i < 1) {
        if (arr[j] > arr[j + 1]) {
            temp = arr[j];
            arr[j] = arr[j + 1];
            arr[j + 1] = temp;
        }
        j++;
        if (j >= 1 - i) {
            j = 0;
            i++;
        }
    }
}
static inline unsigned long read_cycle_count() {
    return rdcycle();
}
int a0 = 0x00000001
;
int a1 = 0x00000000
;int main(int argc, char ** argv)
{
  unsigned long long start;
  unsigned long long end;
  start = read_cycle_count();
  bubble_sort(a0, a1);
  end = read_cycle_count();
  printf("%i\n", (uint32_t) (end - start));
  return 0;
}

