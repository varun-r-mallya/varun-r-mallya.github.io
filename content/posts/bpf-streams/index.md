---
title: Talking about BPF Streams
date: 2026-03-19
author: Varun R Mallya
description: I try my best to analyze BPF Streams
tags:
  - BPF
  - Kernel
  - new stuff
toc: false
---
I was reading the `verifier.c` file when I found `BPF_FEAT_STREAMS` specifically mentioned in the `bpf_features` enum.

So, I blamed the line to find:

```git
commit 5ab154f1463a111e1dc8fd5d31eaa7a2a71fe2e6
Author: Kumar Kartikeya Dwivedi <memxor@gmail.com>
Date:   Thu Jul 3 13:48:08 2025 -0700

    bpf: Introduce BPF standard streams

    Add support for a stream API to the kernel and expose related kfuncs to
    BPF programs. Two streams are exposed, BPF_STDOUT and BPF_STDERR. These
    can be used for printing messages that can be consumed from user space,
    thus it's similar in spirit to existing trace_pipe interface.
```

Let me interject here. So, they made a streaming API. It helps print stuff from BPF programs. Alright, simple. I want to now know why they could not do the same thing with 
`trace_pipe` honestly. Maybe because they needed separate stuff for STDOUT and STDERR or maybe because the trace pipe thing isn't very stable (as I experienced when I moved between 6.18 and 7.0).

```
    The kernel will use the BPF_STDERR stream to notify the program of any
    errors encountered at runtime. BPF programs themselves may use both
    streams for writing debug messages. BPF library-like code may use
    BPF_STDERR to print warnings or errors on misuse at runtime.
```

So the author made this thinking about future BPF library code (which is kinda genius) which could use these streams.
Maybe I should try writing a BPF library ???!!! (I have an idea for a floating point library (a joke honestly) but could actually be useful, who knows ?)

```
    The implementation of a stream is as follows. Everytime a message is
    emitted from the kernel (directly, or through a BPF program), a record
    is allocated by bump allocating from per-cpu region backed by a page
    obtained using alloc_pages_nolock(). This ensures that we can allocate
    memory from any context. The eventual plan is to discard this scheme in
    favor of Alexei's kmalloc_nolock() [0].    
    The kernel will use the BPF_STDERR stream to notify the program of any
    errors encountered at runtime. BPF programs themselves may use both
    streams for writing debug messages. BPF library-like code may use
    BPF_STDERR to print warnings or errors on misuse at runtime.
```

Ok so big words. Lemme break it down. Asking ye ol' Gemini yields:
>✦ The implementation of a "stream" in BPF (as described in your text and reflected in the kernel/bpf/stream.c file) is a specialized, lock-safe logging mechanism designed for the kernel's
>most restrictive execution environments.
>
>1. The Core Purpose: Context-Safe Logging
>BPF programs often run in "atomic" or "emergency" contexts where standard kernel functions like printk() or kmalloc() are unsafe. These include:

>* NMI (Non-Maskable Interrupts): Where a deadlock would occur if the code tried to acquire a spinlock already held by the interrupted task.
>* HardIRQ/Scheduler paths: Where sleeping or blocking is strictly forbidden.
>The "stream" provides two logical channels, BPF_STDOUT and BPF_STDERR, to allow programs and the kernel to emit diagnostic data (strings, stack traces, error codes) without risking a system
>crash or deadlock.
>
>2. Allocation Strategy: From "Bump" to kmalloc_nolock
>The text describes an evolution in how the memory for these messages is managed:
>* The Initial/Old Scheme: It used a "bump allocator" on per-CPU pages obtained via alloc_pages_nolock(). This is essentially a pointer that moves forward in a pre-allocated block of
>memory—extremely fast and requires no locks, but inflexible.
>* The Current Scheme (kmalloc_nolock): As seen in the codebase, the implementation has moved to Alexei Starovoitov's kmalloc_nolock(). This is a sophisticated allocator that provides
>kmalloc-like functionality but uses lockless primitives (such as cmpxchg) instead of standard spinlocks, making it safe to call from NMIs.
>
>3. Logical Streams: STDOUT vs  
>* BPF_STDERR (The Kernel's Voice): This is primarily used by the kernel to report runtime exceptions to the BPF program (and the user). If a program attempts a division by zero or an
>out-of-bounds access that the verifier couldn't catch statically, the kernel "emits" an error message to this stream.
>* BPF_STDOUT (The Program's Voice): Used by developers for standard debugging (e.g., via bpf_stream_printk).
>* Library Use: Shared BPF libraries can use BPF_STDERR to log warnings about API misuse or internal state corruption at runtime, similar to how a user-space library might write to stderr.
>
>4. Data Flow and Structures
>* struct bpf_stream_elem: Every message is wrapped in this structure, which contains the string data and a lockless list node.
>* llist (Lockless Link List): Elements are pushed into a per-program llist. This ensures that multiple CPUs can write to the stream simultaneously without contention.
>* Consumption: The messages are eventually aggregated and can be read back (often through a file descriptor or a specialized BPF link) into user space for analysis.
>
>In summary, this stream implementation is a high-reliability diagnostic pipe that guarantees "always-on" logging visibility even when the kernel is in its most sensitive states.

Honestly, pretty clear explanation of the big wall of words. I have nothing to add to that.

```
    The implementation of a stream is as follows. Everytime a message is
    emitted from the kernel (directly, or through a BPF program), a record
    is allocated by bump allocating from per-cpu region backed by a page
    obtained using alloc_pages_nolock(). This ensures that we can allocate
    memory from any context. The eventual plan is to discard this scheme in
    favor of Alexei's kmalloc_nolock() [0].
```

As explained by ye ol' Gemini, you cannot do normal kernel things like kmalloc or something inside the NMI. At this point in time, they haven't really come to use `kmalloc_nolock()` , but I believe they did it (have to check though) between the time I wrote this and the author wrote the commit.

```
    This record is then locklessly inserted into a list (llist_add()) so
    that the printing side doesn't require holding any locks, and works in
    any context. Each stream has a maximum capacity of 4MB of text, and each
    printed message is accounted against this limit.
```

I learnt a few things from this. You cannot do normal kernel stuff when inside the BPF context. You need to make sure you aren't any pre-acquired spinlocks and that you can only write 1 page worth of stuff here.

```
    Messages from a program are emitted using the bpf_stream_vprintk kfunc,
    which takes a stream_id argument in addition to working otherwise
    similar to bpf_trace_vprintk.
```



```
    The bprintf buffer helpers are extracted out to be reused for printing
    the string into them before copying it into the stream, so that we can
    (with the defined max limit) format a string and know its true length
    before performing allocations of the stream element.

    For consuming elements from a stream, we expose a bpf(2) syscall command
    named BPF_PROG_STREAM_READ_BY_FD, which allows reading data from the
    stream of a given prog_fd into a user space buffer. The main logic is
    implemented in bpf_stream_read(). The log messages are queued in
    bpf_stream::log by the bpf_stream_vprintk kfunc, and then pulled and
    ordered correctly in the stream backlog.

    For this purpose, we hold a lock around bpf_stream_backlog_peek(), as
    llist_del_first() (if we maintained a second lockless list for the
    backlog) wouldn't be safe from multiple threads anyway. Then, if we
    fail to find something in the backlog log, we splice out everything from
    the lockless log, and place it in the backlog log, and then return the
    head of the backlog. Once the full length of the element is consumed, we
    will pop it and free it.

    The lockless list bpf_stream::log is a LIFO stack. Elements obtained
    using a llist_del_all() operation are in LIFO order, thus would break
    the chronological ordering if printed directly. Hence, this batch of
    messages is first reversed. Then, it is stashed into a separate list in
    the stream, i.e. the backlog_log. The head of this list is the actual
    message that should always be returned to the caller. All of this is
    done in bpf_stream_backlog_fill().

    From the kernel side, the writing into the stream will be a bit more
    involved than the typical printk. First, the kernel typically may print
    a collection of messages into the stream, and parallel writers into the
    stream may suffer from interleaving of messages. To ensure each group of
    messages is visible atomically, we can lift the advantage of using a
    lockless list for pushing in messages.

    To enable this, we add a bpf_stream_stage() macro, and require kernel
    users to use bpf_stream_printk statements for the passed expression to
    write into the stream. Underneath the macro, we have a message staging
    API, where a bpf_stream_stage object on the stack accumulates the
    messages being printed into a local llist_head, and then a commit
    operation splices the whole batch into the stream's lockless log list.

    This is especially pertinent for rqspinlock deadlock messages printed to
    program streams. After this change, we see each deadlock invocation as a
    non-interleaving contiguous message without any confusion on the
    reader's part, improving their user experience in debugging the fault.

    While programs cannot benefit from this staged stream writing API, they
    could just as well hold an rqspinlock around their print statements to
    serialize messages, hence this is kept kernel-internal for now.

    Overall, this infrastructure provides NMI-safe any context printing of
    messages to two dedicated streams.

    Later patches will add support for printing splats in case of BPF arena
    page faults, rqspinlock deadlocks, and cond_break timeouts, and
    integration of this facility into bpftool for dumping messages to user
    space.

      [0]: https://lore.kernel.org/bpf/20250501032718.65476-1-alexei.starovoitov@gmail.com

    Reviewed-by: Eduard Zingerman <eddyz87@gmail.com>
    Reviewed-by: Emil Tsalapatis <emil@etsalapatis.com>
    Signed-off-by: Kumar Kartikeya Dwivedi <memxor@gmail.com>
    Link: https://lore.kernel.org/r/20250703204818.925464-3-memxor@gmail.com
    Signed-off-by: Alexei Starovoitov <ast@kernel.org>
```


```
