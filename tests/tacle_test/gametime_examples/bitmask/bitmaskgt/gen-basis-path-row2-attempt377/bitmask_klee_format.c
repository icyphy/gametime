#include </opt/homebrew/include/klee/klee.h>
#include <stdbool.h>

#include <stdint.h>

bool conditional_var_0 = false;
bool conditional_var_1 = false;
bool conditional_var_2 = false;
bool conditional_var_3 = false;
bool conditional_var_4 = false;
bool conditional_var_5 = false;
bool conditional_var_6 = false;
bool conditional_var_7 = false;
bool conditional_var_8 = false;
bool conditional_var_9 = false;
bool conditional_var_10 = false;
bool conditional_var_11 = false;
bool conditional_var_12 = false;
bool conditional_var_13 = false;
bool conditional_var_14 = false;
bool conditional_var_15 = false;
bool conditional_var_16 = false;
bool conditional_var_17 = false;
bool conditional_var_18 = false;
bool conditional_var_19 = false;
bool conditional_var_20 = false;
bool conditional_var_21 = false;
bool conditional_var_22 = false;
bool conditional_var_23 = false;
bool conditional_var_24 = false;
bool conditional_var_25 = false;
bool conditional_var_26 = false;
bool conditional_var_27 = false;
bool conditional_var_28 = false;
bool conditional_var_29 = true;
bool conditional_var_30 = true;
bool conditional_var_31 = true;
bool conditional_var_32 = true;
bool conditional_var_33 = true;
bool conditional_var_34 = true;
bool conditional_var_35 = true;
bool conditional_var_36 = true;
bool conditional_var_37 = true;
bool conditional_var_38 = true;

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


int main() {
    int x;
    klee_make_symbolic(&x, sizeof(x), "x");
    bitmask(x);
    klee_assert(conditional_var_0);
    klee_assert(conditional_var_1);
    klee_assert(conditional_var_2);
    klee_assert(conditional_var_3);
    klee_assert(conditional_var_4);
    klee_assert(conditional_var_5);
    klee_assert(conditional_var_6);
    klee_assert(conditional_var_7);
    klee_assert(conditional_var_8);
    klee_assert(conditional_var_9);
    klee_assert(conditional_var_10);
    klee_assert(conditional_var_11);
    klee_assert(conditional_var_12);
    klee_assert(conditional_var_13);
    klee_assert(conditional_var_14);
    klee_assert(conditional_var_15);
    klee_assert(conditional_var_16);
    klee_assert(conditional_var_17);
    klee_assert(conditional_var_18);
    klee_assert(conditional_var_19);
    klee_assert(conditional_var_20);
    klee_assert(conditional_var_21);
    klee_assert(conditional_var_22);
    klee_assert(conditional_var_23);
    klee_assert(conditional_var_24);
    klee_assert(conditional_var_25);
    klee_assert(conditional_var_26);
    klee_assert(conditional_var_27);
    klee_assert(conditional_var_28);
    klee_assert(conditional_var_29);
    klee_assert(conditional_var_30);
    klee_assert(conditional_var_31);
    klee_assert(conditional_var_32);
    klee_assert(conditional_var_33);
    klee_assert(conditional_var_34);
    klee_assert(conditional_var_35);
    klee_assert(conditional_var_36);
    klee_assert(conditional_var_37);
    klee_assert(conditional_var_38);
    return 0;
}