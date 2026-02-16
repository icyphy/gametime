#ifndef KLEE_KLEE_H
#define KLEE_KLEE_H

#include <stddef.h>

/* Stub implementations of KLEE functions for compilation without KLEE */
static void klee_make_symbolic(void *addr, size_t nbytes, const char *name) {
    (void)addr; (void)nbytes; (void)name;
}

static void klee_assert(int condition) {
    (void)condition;
}

static int klee_range(int start, int end, const char *name) {
    (void)name;
    return start;
}

#endif /* KLEE_KLEE_H */
