#include <stdio.h>
#include <stdlib.h>

int main() {
    int x = 5;
    int y = 10;
    char buffer[20];

    printf("Before modification:\n");
    printf("x = %d\n", x);
    printf("y = %d\n", y);

    // Convert integers to strings
    sprintf(buffer, "%d", x);
    // Append some digits to the string representation of x
    strcat(buffer, "123");
    // Convert back to integer
    x = strtol(buffer, NULL, 10);

    // Convert integers to strings
    sprintf(buffer, "%d", y);
    // Append some digits to the string representation of y
    strcat(buffer, "456");
    // Convert back to integer
    y = strtol(buffer, NULL, 10);

    printf("After modification:\n");
    printf("x = %d\n", x);
    printf("y = %d\n", y);

    return 0;
}
