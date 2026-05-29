---
title: Analysis of BPF JIT in general.
date: 2026-05-25
author: Varun R Mallya
description: I try to understand some weird functions.
tags:
  - BPF
  - Kernel
  - JIT
toc: false
---

I'll be analysing BPF JIT today.
I'll be doing a bottom up approach today.
- `bpf_int_jit_compile()` is the function found inside the JIT for arm64 at `arch/<architecture>/net/bpf_jit_comp.c` or equivalent.
-  

