---
title: Discovering x-macros
date: 2026-03-17
author: Varun R Mallya
description: I try my best to learn about x-macros.
tags:
  - C
  - patterns
  - fundamentals
toc: false
---
I found this weird pattern I did not understand in the kernel:

```c
static const struct bpf_verifier_ops * const bpf_verifier_ops[] = {
#define BPF_PROG_TYPE(_id, _name, prog_ctx_type, kern_ctx_type) \
	[_id] = & _name ## _verifier_ops,
#define BPF_MAP_TYPE(_id, _ops)
#define BPF_LINK_TYPE(_id, _name)
#include <linux/bpf_types.h>
#undef BPF_PROG_TYPE
#undef BPF_MAP_TYPE
#undef BPF_LINK_TYPE
};
```

I found out that these are [X-Macros](https://en.wikipedia.org/wiki/X_macro) along with C99-Designated-Initializers.
So, X Macros are a pattern of using programming language macros to generate list like structures.

> An X macro application consists of two parts:
>
>    1. The definition of the list's elements.
>    2. Expansion(s) of the list to generate fragments of declarations or statements.
> 
> The list is defined by a macro or header file (named, LIST) which generates no code by itself, but merely consists of a sequence of invocations of a macro (classically named "X") with the elements' data. Each expansion of LIST is preceded by a definition of X with the syntax for a list element. The invocation of LIST expands X for each element in the list. 

So here, it gets the stuff form `bpf_types.h` and runs these multitudes of macros on it and it turns into an initializer list that shows all the programs.
