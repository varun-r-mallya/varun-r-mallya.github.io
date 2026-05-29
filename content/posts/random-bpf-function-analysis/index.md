---
title: Specific commit analysis in BPF
date: 2026-05-25
author: Varun R Mallya
description: I try to understand some weird functions.
tags:
  - BPF
  - Kernel
  - arguments
toc: false
---
# `struct bpf_reg_state` (`kernel/bpf/bpf_verifier.h`)
Ok so this isn't really a function, but rather a struct. First line inside of it states that ordering of fields matter. And then it references another function present inside of `states.c` called `states_equal()`. We first do an internal analysis of this function.
## struct states_equal()

