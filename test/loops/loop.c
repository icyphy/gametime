
int test(){
    int result = 0;
    // #pragma clang loop unroll(full)
    #pragma unroll(3)
    for (int i = 0; i < 2; i++) {
        result += i;
    }

    return result;
}