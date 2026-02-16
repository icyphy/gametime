int abs_val(int x) {
    if (x < 0) return -x;
    return x;
}

int test(int x){
    if (abs_val(x) == 4) {
        return 0;
    } else {
        return 1;
    }
}
