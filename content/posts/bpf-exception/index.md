---
title: Getting BPF exceptions RISC-V JIT support
date: 2026-05-03
author: Varun R Mallya
description: I try to add exceptions to RISC-V JIT
tags:
  - BPF
  - Kernel
  - new stuff
toc: false
---

Ok, so I recently landed this: [damn das a patch](https://lore.kernel.org/bpf/20260602205847.102825-1-varunrmallya@gmail.com/)  
I did this because I saw [this](https://lore.kernel.org/bpf/20260513044949.2382019-1-yonghong.song@linux.dev/) and I then wanted to add arm64 support to it. But Puranjay added it so fast that my dumb head had no time at all to add this out. Then, I tried to add riscv support for it, but once I got testing ready, I realised that the selftests did not work at all because exceptions, which were present in the tests I was running were not there on RISC-V, so that eventually turned into my first goal.
Now, I've throughly dealth with RISC-V JIT and the nuances of cross compiling, which is somehow pretty hard. I'd really like someone to build cross compilation containers maybe (or they probably do and I just dont know)
This blog will show how I analyze stuff to write a patchset.

First things first, I wrote the patch improving RISC-V not only to gain experience with the JIT before working on it, but to also get the testing env set up as well as the compilation toolchain + scripts to load it into virtme-ng.

Let me briefly describe this process:  
> Note: I have begun to use AI agents a lot in my current workflows to improve my speed, since I also have to do other stuff. It also makes it much easier to focus on the real details and lets me cut through the noise.

I first asked an agent to show me and all ways to run tests on RISC-V. Me being the broke student I am, cannot afford a RISC-V board worth 30-40 USD, so QEMU it is.
Then, I asked it if test scripts existed on the kernel and I got a resounding yes in the form of `vmtest.sh`. Look up the usage yourself, but it's amazing and the most objective way to do this kind of work.
Also, get all the needed libraries installed in your RISC-V sysroot like openssl, libelf etc. compiled for RISC-V. Then, I also got myself a rootfs to boot with using virtme-ng which I had a LOT OF ISSUES doing an `apt update` on because of the weird authentication error on the outdated keyring inside of it, which I found no solution for and added a rule to ignore authentication, since it's just a test environment and I totally love security.  
Then, it was go time. I managed to see exactly what Puranjay had done on a similar patch for arm64 and managed to replicate something similar to that for RISC-V and.... it messed up during testing. Turns out that no one had thought of adding CPU and feature flags to the JIT disassembler inside of bpftool as well as the `test_progs` binary. I then added that, since it was missing for the weird "+c" Compressed Instruction extension to RISC-V ISA. Both the patch and the test worked flawlessly and ran smoothly after which I submitted it and Björn acked it.

That's all old stuff now. Now we come to adding new things. 
Ok, so I sent out an agent to analyze commits and get me the places where exception support was added by Kartikeya Kumar Dwivedi and the corresponding arm64 support by Puranjay. It gave me this:

```md
Commits to read, in order

1. Core infrastructure (arch-agnostic)

f18b03fabaa9 — "bpf: Implement BPF exceptions"

This is the foundational commit. Read it for:
- kernel/bpf/helpers.c: bpf_throw() + bpf_stack_walker() — this is the runtime. At throw time it walks the kernel stack via arch_bpf_stack_walk, finds the BPF prog marked as exception_boundary, then calls aux->bpf_exception_cb(cookie, sp, bp, 0, 0). The callback receives (cookie, sp, fp) as its first three args.
- include/linux/bpf.h:1750 — the bpf_exception_cb function pointer and stack_arg_sp_adjust in bpf_prog_aux
- kernel/bpf/verifier.c — how the verifier sets exception_boundary and exception_cb flags and calls add_hidden_subprog

This commit only lands the x86 JIT side. Read those x86 changes to understand the pattern.

2. x86 JIT (first JIT implementation — the reference)

Still in f18b03fabaa9, file arch/x86/net/bpf_jit_comp.c:

The key structural changes are:
- all_callee_regs_used[4] = {true,true,true,true} — a static "pretend all callee regs are used" mask
- push_r12 / pop_r12 — r12 is callee-saved but not mapped to any BPF reg, so it could be clobbered by the kernel inside bpf_throw; the boundary prog must save it too
- emit_prologue(..., bool is_exception_cb) — for exception_cb progs: instead of pushing a new frame, receive rsi=sp and rdx=fp from the call, pop callee regs from the boundary prog's stack, then reset rsp=rbp
- do_jit: if exception_boundary, use all_callee_regs_used (force-save everything) and also push_r12
- tail-call paths: same force-pop for boundary progs
- bpf_jit_supports_exceptions() at line 4105 — returns IS_ENABLED(CONFIG_UNWINDER_ORC)
- arch_bpf_stack_walk() at line 4119 — uses the ORC unwinder

3. Fix for stack arguments

18a37465b0ab — "bpf,x86: Fix exception unwinding with outgoing stack arguments"

Read this because the stack_arg_sp_adjust field in bpf_prog_aux adjusts sp before calling the callback when the boundary prog passes stack args. Minor but you'll need this for correctness.

4. ARM64 JIT (your closest model for RISC-V)

22fc0e80aeb5 — "bpf, arm64: support exceptions"

This is the best analog for RISC-V. ARM64 also uses a frame pointer unwinder (not ORC). Read arch/arm64/net/bpf_jit_comp.c diffs:

- build_prologue(..., bool is_exception_cb):
  - If exception_boundary: push_callee_regs saves all arm64 callee-saved regs (r19–r28)
  - If is_exception_cb: receive fp as 3rd arg (A64_R(2)), set sp = fp - 96 (10 regs × 8 + r23/r24 pair = boundary prog's frame)
- build_epilogue(..., bool is_exception_cb):
  - If exception_boundary || is_exception_cb: pop all callee-saved regs (both cases need the full restore)
- bpf_jit_supports_exceptions() — returns true unconditionally because arm64 always has CONFIG_FRAME_POINTER=y
- arch_bpf_stack_walk() in arch/arm64/kernel/stacktrace.c:437 — uses kunwind_stack_walk

5. ARM64 fixup (important)

b114fcee766d — "bpf, arm64: Fix fp initialization for exception boundary"

Fixes a bug where fp wasn't being set properly in the exception boundary prologue. Read this too.

---
What you need to implement for RISC-V

File: arch/riscv/net/bpf_jit_comp64.c

Register situation (the analog to x86's r12 / arm64's r23+r24):

Current BPF register mapping uses: s1–s7 (BPF regs 6–9, fp, TCC_SAVED, arena). That leaves s8 (24), s9 (25), s10 (26), s11 (27) as callee-saved but unused by BPF. These could be clobbered on the bpf_throw kernel entry path, so the exception boundary prog must save them.

Changes to bpf_jit_build_prologue (line 1995):
- Add bool is_exception_cb parameter
- If prog->aux->exception_boundary: force-save ALL s-regs (s1–s11 + ra + fp), not just the seen_reg() subset; then also save s8–s11 which are normally never saved
- If is_exception_cb: receive the boundary prog's FP in a2 (3rd argument per RISC-V ABI), set fp = a2, set sp = fp - (boundary_frame_size), skip pushing a new frame entirely

Changes to __build_epilogue (line 231):
- If prog->aux->exception_boundary || is_exception_cb: restore all callee-saved regs (the full set), not just seen_reg() ones

Add bpf_jit_supports_exceptions():
bool bpf_jit_supports_exceptions(void)
{
    return IS_ENABLED(CONFIG_FRAME_POINTER);
}
RISC-V's stacktrace.c uses walk_stackframe only under CONFIG_FRAME_POINTER (see arch/riscv/kernel/stacktrace.c:17), so this must be the guard.

New function: arch_bpf_stack_walk() in arch/riscv/kernel/stacktrace.c (or bpf_jit_comp64.c)

Model it after the arm64 version but call walk_stackframe:
void arch_bpf_stack_walk(bool (*consume_fn)(void *, u64, u64, u64), void *cookie)
{
#ifdef CONFIG_FRAME_POINTER
    walk_stackframe(current, NULL, /* adapter callback */ ...);
#endif
}
The adapter needs to convert walk_stackframe's (arg, pc) signature into (cookie, ip, sp, bp) — look at how powerpc does it in arch/powerpc/net/bpf_jit_comp64.c:426 as another reference since it also wraps a frame-pointer walk.

---
Reading order summary

┌─────┬──────────────┬───────────────────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│  #  │    Commit    │                 File                  │                                                            Why                                                             │
├─────┼──────────────┼───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 1   │ f18b03fabaa9 │ kernel/bpf/helpers.c                  │ Understand bpf_throw runtime: stack walk → find boundary → call cb with (cookie, sp, fp)                                   │
├─────┼──────────────┼───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 2   │ f18b03fabaa9 │ include/linux/bpf.h:1750              │ bpf_exception_cb signature, exception_boundary/exception_cb flags, stack_arg_sp_adjust                                     │
├─────┼──────────────┼───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 3   │ f18b03fabaa9 │ arch/x86/net/bpf_jit_comp.c           │ First JIT impl: how exception_boundary forces all callee saves + extra r12, how exception_cb prologue reuses boundary's    │
│     │              │                                       │ frame                                                                                                                      │
├─────┼──────────────┼───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 4   │ 18a37465b0ab │ arch/x86/net/bpf_jit_comp.c           │ stack_arg_sp_adjust usage — sp offset correction when boundary prog has outgoing stack args                                │
├─────┼──────────────┼───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 5   │ 22fc0e80aeb5 │ arch/arm64/net/bpf_jit_comp.c         │ ARM64 port — closest analog to RISC-V, frame-pointer based, push_callee_regs all-vs-selective pattern                      │
├─────┼──────────────┼───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 6   │ b114fcee766d │ arch/arm64/net/bpf_jit_comp.c         │ FP init bug fix — don't miss this                                                                                          │
├─────┼──────────────┼───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 7   │ Current      │ arch/riscv/net/bpf_jit_comp64.c:1995  │ bpf_jit_build_prologue — where you add is_exception_cb and the boundary path                                               │
├─────┼──────────────┼───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 8   │ Current      │ arch/riscv/net/bpf_jit_comp64.c:231   │ __build_epilogue — where you add the all-regs restore path                                                                 │
├─────┼──────────────┼───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 9   │ Current      │ arch/riscv/kernel/stacktrace.c:17     │ Frame pointer walk — the basis for your arch_bpf_stack_walk                                                                │
├─────┼──────────────┼───────────────────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ 10  │ Current      │ arch/powerpc/net/bpf_jit_comp64.c:426 │ arch_bpf_stack_walk for a non-ORC arch — alternative model                                                                 │
└─────┴──────────────┴───────────────────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

The arm64 commit (22fc0e80aeb5) is your primary template since RISC-V and arm64 share the same fundamental constraint: frame-pointer-based unwinding, callee-saved reg sets that partially overlap with the BPF register map, and a 3rd-argument convention for passing the boundary program's FP to the exception callback.
```
