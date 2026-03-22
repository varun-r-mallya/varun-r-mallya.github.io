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
- Time to find out how to trigger this.

## How is refcount variable decided
- The argument name should end with a `__ref`.
- Refcounting a variable means that variable is acquired by the BPF program.
- Somehow we are "responsible" for it's lifecycle. (I need to find out what this means)
- Tail calls are not allowed in progs with refcounted arguments that you don't know if that reference will ever be dropped across programs.
- 

## Triggering the error 
- Something I understand here is that I cannot "craft" BTF since they are generated from kernel structs.
- But then, there is something in selftests that I can use at `tools/testing/selftests/bpf/test_kmods/bpf_testmod.h`.
- Gemini says (and I agree):
> 
> The bug exists because the loop checks info->refcounted (which is always info[0]). To trigger it, you need a scenario where:
>   1. The first annotated argument is NOT refcounted (e.g., it's __nullable).
>   2. A later annotated argument IS refcounted (__ref).
- The bug was successfully identified and fixed by the author.
- I just need to write the selftest.

## Actually writing the selftest
- I found `bpf_testmod.h` and `bpf_testmod.c`.
- *bpf_testmod* is a kernel module specifically designed for BPF testing.
- `bpf_testmod.ko` is made and loaded into the kernel for BPF testing.
- I need to add the thing lines to make the data structure to test as well as the stub function.
```c

diff --git a/tools/testing/selftests/bpf/test_kmods/bpf_testmod.c b/tools/testing/selftests/bpf/test_kmods/bpf_testmod.c
index 94edbd2afa67..da48855f6285 100644
--- a/tools/testing/selftests/bpf/test_kmods/bpf_testmod.c
+++ b/tools/testing/selftests/bpf/test_kmods/bpf_testmod.c
@@ -1411,6 +1411,12 @@ static int bpf_testmod_ops__test_refcounted(int dummy,
 	return 0;
 }
 
+static int bpf_testmod_ops__test_multiple_args(struct task_struct *task__nullable,
+					       struct task_struct *task__ref)
+{
+	return 0;
+}
+
 static struct task_struct *
 bpf_testmod_ops__test_return_ref_kptr(int dummy, struct task_struct *task__ref,
 				      struct cgroup *cgrp)
@@ -1423,6 +1429,7 @@ static struct bpf_testmod_ops __bpf_testmod_ops = {
 	.test_2 = bpf_testmod_test_2,
 	.test_maybe_null = bpf_testmod_ops__test_maybe_null,
 	.test_refcounted = bpf_testmod_ops__test_refcounted,
+	.test_multiple_args = bpf_testmod_ops__test_multiple_args,
 	.test_return_ref_kptr = bpf_testmod_ops__test_return_ref_kptr,
 };
 
diff --git a/tools/testing/selftests/bpf/test_kmods/bpf_testmod.h b/tools/testing/selftests/bpf/test_kmods/bpf_testmod.h
index f6e492f9d042..0cbc35e3ee86 100644
--- a/tools/testing/selftests/bpf/test_kmods/bpf_testmod.h
+++ b/tools/testing/selftests/bpf/test_kmods/bpf_testmod.h
@@ -39,6 +39,8 @@ struct bpf_testmod_ops {
 	int (*unsupported_ops)(void);
 	/* Used to test ref_acquired arguments. */
 	int (*test_refcounted)(int dummy, struct task_struct *task);
+	/* Used to test checking of __ref arguments when it not the first argument. */
+	int (*test_multiple_args)(struct task_struct *task__nullable, struct task_struct *task__ref);
 	/* Used to test returning referenced kptr. */
 	struct task_struct *(*test_return_ref_kptr)(int dummy, struct task_struct *task,
 						    struct cgroup *cgrp);
```
- The above is what I came up with to add this test.
- I then added a BPF program that keeps the reference and does not drop it. 
- voila. submitted.

Final Patch: [lore.kernel.org](https://lore.kernel.org/bpf/9f8cc4f1-a603-4cbf-9c99-1f5bca341ca5@inria.fr/T/#m7afbce5638dc0a2361901a51b881cdd1412931fb)
