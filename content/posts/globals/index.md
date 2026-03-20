---
title: How the Kernel handles globals
date: 2026-03-20
author: Varun R Mallya
description: I present a basic understanding of how globals are handled in the kernel.
tags:
  - Globals
  - Kernel
  - fundamentals
toc: false
---
I was going through verifier.c and found a peculiar global variable `struct btf *btf_vmlinux`. It is handled across the code by putting a mutex on it's writes. 
Although I knew how the kernel's ELF structure is handled, I still had no proper sense of how close it was to normal ELF structures and that the `vmlinux` found in /boot is literally just an ELF that is fully valid.
Asking LLMs yields the following big words:
	- re-entrant
	- supports symmetric multiprocessing
I also found out that there is a small "bootloader" stub that decompresses the kernel first before doing all the other stuff.

## NOTE:
This blog, like all the blogs in this series is dynamic. It will keep being updated. This article is a stub.
