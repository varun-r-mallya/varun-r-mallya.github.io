---
title: Cooking into the eBPF verifier
date: 2026-03-19
author: Varun R Mallya
description: I try my best to analyze the verifier from the beginning now
tags:
  - BPF
  - Kernel
  - fundamentals
  - verifier
---

# The goal
Rn, we gotta understand the working of the verifier and hopefully find errors.

# bpf_check
This is the holy grail where it all starts.
- `bpf_verifier_env` is similarly the holy grail struct where it all begins.
- `bpf_features` I still do not fully understand this enum, although I know it talks about readonly memory and bpf streams.
- `kvzalloc_obj` this is a kernel malloc variant that either allocates physically contiguous memory as `kmalloc`, or then falls back to `vmalloc` that gives virtually contiguous memory. The `z` also zeros out stuff. `_obj` means type safe wrapper that auto-calculates the size. 
- `iarray_realloc` is a genius move. It keeps in mind both the branches of an if condition and preallocates both the branches of this so no reallocation needs to be done.
- There is some amount of code here to take bpf tokens and get some capability information from that.
```c
	env->allow_ptr_leaks = bpf_allow_ptr_leaks(env->prog->aux->token);
	env->allow_uninit_stack = bpf_allow_uninit_stack(env->prog->aux->token);
	env->bypass_spec_v1 = bpf_bypass_spec_v1(env->prog->aux->token);
	env->bypass_spec_v4 = bpf_bypass_spec_v4(env->prog->aux->token);
	env->bpf_capable = is_priv = bpf_token_capable(env->prog->aux->token, CAP_BPF);

```
- As you can see, there are two kinds of spectre mitigations for v1 and v4. This does `spectre masking`. v1 does mitigations for a bounds check bypass and v4 makes mitigations for speculative store bypass.
- `bpf_get_btf_vmlinux();` this is then run. The verifier lock is acquired and then `btf_parse_vmlinux` is run.
- So, btf_parse_vmlinux has a few jobs:
	- It checks the .BTF section of the linux kernel
	- It then checks for the __start_BTF and __stop_BTF linker symbols and uses them to parse and put that BTF info into memory.
	- As far as I am able to infer, this happens on every goddamn verification not happening concurrently/paralelly, which seems kinda wasteful, but they must have their reasons idk.


