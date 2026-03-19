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


