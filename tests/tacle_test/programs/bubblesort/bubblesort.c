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