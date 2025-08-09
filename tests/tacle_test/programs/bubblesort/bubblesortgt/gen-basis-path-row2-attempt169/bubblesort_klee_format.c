#include </opt/homebrew/include/klee/klee.h>
#include <stdbool.h>


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
bool conditional_var_17 = true;
bool conditional_var_18 = true;
bool conditional_var_19 = true;
bool conditional_var_20 = true;
bool conditional_var_21 = true;
bool conditional_var_22 = true;

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
int main() {
    int a0;
    klee_make_symbolic(&a0, sizeof(a0), "a0");
    int a1;
    klee_make_symbolic(&a1, sizeof(a1), "a1");
    bubble_sort(a0, a1);
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
    return 0;
}