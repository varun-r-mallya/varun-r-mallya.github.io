---
title: Adding a selftest for someone else's fix
date: 2026-03-21
author: Varun R Mallya
description: I try to add a selftest to a particular fix made by someone on the verifier.
tags:
  - BPF
  - Kernel
  - verifier
toc: false
---

Note: This will be a casual blog, so excuse my language. It's mostly stuff for documentation (for my brain).

# The goal 
- [lore.kernel.org](https://lore.kernel.org/bpf/CAMB2axOSUF9MnYnKZiBNpGMi_Ay81Ph3T6L83yG3g9A=2grNCQ@mail.gmail.com/T/#t) is the conversation I came across earlier today.
- I want to quickly send in a selftest before the original author does to better my understanding of the verifier.

# Finding out what the fix actually did

We will be doing this by backtracing from the function to the function I am familiar with, `bpf_check`, then we will be finding out how to hit this function by writing a relevant selftest. We will first check if there exists something similar to the selftest we want already, and if it does, we will maybe extend it.

## "Backtracing"
```c

	for (i = 0; i < st_ops_desc->arg_info[member_idx].cnt; i++) {
```
- A few things, `st_ops_desc` is a struct of type `bpf_struct_ops_desc` and arg_info is of the type `bpf_struct_ops_arg_info`
```c

struct bpf_struct_ops_arg_info {
	struct bpf_ctx_arg_aux *info;
	u32 cnt;
};
```
- That is the info field we want.
```c

/* reg_type info for ctx arguments */
struct bpf_ctx_arg_aux {
	u32 offset;
	enum bpf_reg_type reg_type;
	struct btf *btf;
	u32 btf_id;
	u32 ref_obj_id;
	bool refcounted;
};
```
Here is the refcounted field we need to target.
- The source of the first struct here is from 
```c
	st_ops_desc = bpf_struct_ops_find(btf, btf_id);
```
- From the arguments, we can clearly see that this is a consequence of BTF.
- This clearly means that we need to craft BTF that break this.
- The following is the struct hierarchy that we need to target.
- `bpf_struct_ops_desc` -> `bpf_struct_ops_arg_info` -> `bpf_ctx_arg_aux` -> (field)`bool refcounted`.
- 
