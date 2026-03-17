---
title: Cooking into BPF internals
date: 2026-03-17
author: Varun R Mallya
description: I try my best to reach the verifier in the flow today.
tags:
  - BPF
  - Kernel
  - fundamentals
---

Note: This will be a casual blog, so excuse my language. It's mostly stuff for documentation (for my brain).

### Za goal 
- My goal today is to start from the syscall and reach verifier.c's entry function.
- After that, I will move on to analyzing verifier.c itself in the next part to this blog series.

# sys_bpf
We start from the very beginning. `sys_bpf` is where everything begins.
- `bpf_check_uarg_tail_zero` runs to check if the size is larger than expected or not.
- Then bpf_attr is moved from userspace to kernelspace
- then `security_bpf` runs on it which checks permissions and whatnot.
- then a whole switch case statement runs that goes and does every job bpf does.
- Since I am trying to get to verifier.c the fastest, I will have to choose `bpf_prog_load` to target today.

# bpf_prog_load
- This is what we will analyze now.
- `bpf_prog_load_fixup_attach_type` this fixes backward compatibility stuff.
- token is then taken from a fd.
- token capability is evaluated through a barrage of stuff
Note to self: If I ever wanna work on tokens, come to `syscall.c`

currently stopped at kernel/bpf/syscall.c:2913
 
