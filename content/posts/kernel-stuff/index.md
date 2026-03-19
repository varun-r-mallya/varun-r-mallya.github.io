---
title: Cooking into BPF internals
date: 2026-03-17
author: Varun R Mallya
description: I try my best to reach the verifier in the flow today.
tags:
  - BPF
  - Kernel
  - fundamentals
toc: false
---

Note: This will be a casual blog, so excuse my language. It's mostly stuff for documentation (for my brain).

# The goal 
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
Note to self: If I ever wanna work on tokens, come to `syscall.c:bpf_prog_load` 
- Unprevileged BPF execution ability checked.
- License is checked
- Then,
```c
	/* run eBPF verifier */
	err = bpf_check(&prog, attr, uattr, uattr_size);
	if (err < 0)
		goto free_used_maps;

	prog = bpf_prog_select_runtime(prog, &err);
	if (err < 0)
		goto free_used_maps;

	err = bpf_prog_mark_insn_arrays_ready(prog);
	if (err < 0)
		goto free_used_maps;

	err = bpf_prog_alloc_id(prog);
	if (err)
		goto free_used_maps;
```
The order in which this is run is pretty cool too.
- `bpf_check` runs the verifier on the program
- `bpf_prog_select_runtime` is what selects the JIT interpreter or the direct interpreter (if I wanna understand JIT and interpretation itself, I need to start from here ig)
Tangent: `IS_ENABLED(CONFIG_BPF_JIT_ALWAYS_ON)` is how kernel config enablement is checked.
- `bpf_insn_array_ready` checks the existence of incomplete instruction arrays so that malformed stuff isn't executed.interpreter

# bpf_check
- We have reached the goal of this post

Tangent:
	- `idr_preload(GFP_KERNEL)` this is preloading the ID mapping allocation in the current context and
	  it goes to the integer ID management part in the kernel that thandoes the ID alocation.
	- `prog_idr`whenever accessed is supposed to be protected by a spinlock.


