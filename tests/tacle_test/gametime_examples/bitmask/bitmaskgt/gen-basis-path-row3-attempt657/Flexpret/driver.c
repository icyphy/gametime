#include <flexpret/flexpret.h> 
#include <stdint.h>

/* Key idea – each bit of x decides whether we call a heavy or light helper.
Worst case: x == 0b1111 (all four bits set) → every loop iteration takes the costly path. */

/* ---- helpers ----------------------------------------------------------- */
static inline int heavy(int k) {
    int s = 0;
    #pragma unroll 3           // fixed 10‑cycle inner loop
    for (int j = 0; j < 3; ++j) {
        s += k * j + 3;         // a few ALU ops
    }
    return s;
}

static inline int light(int k) {
    return k;                   // basically free
}

/* ---- main under analysis ---------------------------------------------- */
int bitmask(int x) {               // single integer argument is the “input”
    int acc = 0;

    #pragma unroll 4
    for (int i = 0; i < 4; ++i) {
        if (x & (1 << i)) {
            acc += heavy(i);    // worst‑case branch
        } else {
            acc += light(i);
        }
    }
    return acc;
}


static inline unsigned long read_cycle_count() {
    return rdcycle();
}
int x = 0x00000004
;int main(int argc, char ** argv)
{
  unsigned long long start;
  unsigned long long end;
  start = read_cycle_count();
  bitmask(x);
  end = read_cycle_count();
  printf("%i\n", (uint32_t) (end - start));
  return 0;
}

