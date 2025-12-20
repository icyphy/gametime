// FIXME: Support header files and move the abs declaration to a helper.h.
int abs(int x); // Defined in helper.c

// Function under analysis
int test(int x){
    if (abs(x) == 42) {
        int a = 1;
        int b = a * 2;
        int c = a * b;
        return c;
    }
    else if (abs(x) == 128) {
        int a = 1;
        int b = a * 2;
        return b;
    }
    return 0;
}



