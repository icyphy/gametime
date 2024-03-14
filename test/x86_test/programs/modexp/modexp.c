int modexp(int base, int exponent) {
    int p = 751; // what is p?
    int result = 1;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
    }
    exponent >>= 1;
    base = (base * base) % p;
    if ((exponent & 1) == 1) {
        result = (result * base) % p;
    }
    exponent >>= 1;
    base = (base * base) % p;
    
    return result;
}