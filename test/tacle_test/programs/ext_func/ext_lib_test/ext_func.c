#include "helper.h"
#include </snap/klee/9/usr/local/include/klee/klee.h>

int ext_func(int x){
    if (abs(x) == 4) {
        return 0;
    } else {
        return 1;
    }
}

int main() {

// ext_func_1
    // int x;
    // klee_make_symbolic(&x, sizeof(x), "x");
    // return ret0(x);

// ext_func_2
    int x;
    klee_make_symbolic(&x, sizeof(x), "x");
    return ext_func(x);
    
}






// clang -emit-llvm -c helper.c -o helper.bc
// clang -emit-llvm -c -g ext_func.c -o ext_func.bc
// klee ext_func.bc
// klee -link-llvm-lib=helper.bc ext_func.bc
// klee.ktest-tool klee-last/test000001.ktest 

// clang -emit-llvm -O0 -c helper.c -o helper.bc
// clang -emit-llvm -O0 -c ext_func.c -o ext_func.bc
// llvm-link ext_func.bc helper.bc -o combined.bc
// opt -always-inline -inline -inline-threshold=10000000 combined.bc -o inlined.bc
// opt -always-inline -inline -inline-threshold=10000000 combined_mod.bc -o inlined.bc
// opt -dot-cfg inlined.bc
// opt -dot-cfg inlined.bc
// dot -Tpng .main.dot -o cfg_main.png

// llvm-dis combined.bc -o combined.ll
// llvm-dis inlined.bc -o inlined.ll
// llvm-as combined.ll -o combined.bc
// llvm-as combined_mod.ll -o combined_mod.bc
// alwaysinline
// clang -O0 combined.ll -o combined.bc



