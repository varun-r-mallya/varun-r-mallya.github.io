// RAS (return address stack) size probe: nested call chain of depth N,
// each level a distinct 16-byte function `call next; ret`. Once N exceeds
// the RAS capacity, the outermost returns mispredict and ns/return jumps.
#define _GNU_SOURCE
#include <stdio.h>
#include <stdint.h>
#include <time.h>

#define MAXD 256

__asm__(
    ".text\n"
    ".balign 16\n"
    "chain_base:\n"
    ".rept " "256" "\n"
    "  call .+16\n"      // call the next 16-byte block
    "  ret\n"
    "  .balign 16\n"
    ".endr\n"
    "  ret\n"
);
extern char chain_base[];

static double now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1e9 + ts.tv_nsec;
}

int main(void) {
    const int iters = 200000, reps = 7;
    printf("depth,ns_per_return\n");
    for (int d = 1; d <= MAXD; d++) {
        void (*fn)(void) = (void (*)(void))(chain_base + 16 * (MAXD - d));
        double best = 1e30;
        for (int r = 0; r < reps; r++) {
            double t0 = now();
            for (int i = 0; i < iters; i++) fn();
            double t = (now() - t0) / iters / (d + 1); // +1 for the outer call
            if (t < best) best = t;
        }
        printf("%d,%.3f\n", d, best);
    }
    return 0;
}
