---
title: Reviewing YongHong's stackable Args patchset
date: 2026-03-20
author: Varun R Mallya
description: I try to understand the changes that YongHong has made on the patchset.
tags:
  - BPF
  - Kernel
  - arguments
toc: false
---

This patch is currently on it's v4 and I'm pretty interested in it because I want to try adding ARM JIT support for it.

BPF is currently limited by 5 arguments due to registers. There is also compiler support to take into account.
This patch takes into account all those changes also putting LLVM support.
My job will probably involve messing with LLVM as well as kernel. Nothing on the verifier side maybe, but let's see. I'll make an aside every time I want to keep arch specific versions in consideration.
- Adds an r12 register (BPF_REG_STACK_ARG_BASE)
- (MAX_BPF_FUNC_ARGS) is where the args are capped at.
- x86_64 JIT translates r12 relative actions to RBP rel native insns.
- each function's stack allocation is ext by max_outgoing bytes (which I don't understand)

Update: I had exams.
This patch is on it's v6 right now and I need to check why things were do as they were. I need to restart. I think v4 had a few arm changes as well but v6 had those removed.

- the first patch does a basic useless variable removal that was probably left from a previous change that forgot to remove it.
- `ptr_regno` was a variable that was passed before to 



## NOTE:
This blog, like all the blogs in this series is dynamic. It will keep being updated. This article is a stub.
