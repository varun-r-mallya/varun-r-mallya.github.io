---
title: Strace with eBPF and Rust
date: 2025-02-01
author: Varun R Mallya
description: How to build an strace-like program with eBPF
tags:
  - eBPF
  - Rust
  - strace
---

# Building an `strace`-like Tool with eBPF and Rust

## Introduction

`strace` is a powerful tool for tracing system calls made by processes. While the traditional `strace` uses the `ptrace` system call, eBPF provides a more efficient, non-intrusive way to achieve the same functionality. In this post, we'll explore how to build a lightweight `strace`-like tool using eBPF and Rust.

## Prerequisites

Ensure the following are installed on your system:

- Linux kernel version 5.4 or higher with eBPF support
- Rust (with `cargo` and `rustup`)
- `bpf` and `clang` tools for compiling eBPF programs
- `bpftool` for debugging eBPF programs

```bash
sudo apt update && sudo apt install -y clang llvm libelf-dev linux-headers-$(uname -r)
cargo install bpf-linker
```

---

## Project Setup

Create a new Rust project:

```bash
cargo new ebpf-strace
cd ebpf-strace
```

Add dependencies in `Cargo.toml`:

```toml
[dependencies]
aya = "0.10"
tokio = { version = "1", features = ["full"] }
clap = { version = "4.0", features = ["derive"] }
```

---

## Writing the eBPF Program

Create an eBPF program to trace `sys_enter` events. In `src/bpf/programs.c`:

```c
#include <vmlinux.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>

char LICENSE[] SEC("license") = "GPL";

SEC("tracepoint/syscalls/sys_enter")
int trace_sys_enter(struct trace_event_raw_sys_enter *ctx) {
    int syscall_id = ctx->id;
    bpf_printk("PID %d called syscall ID %d", bpf_get_current_pid_tgid() >> 32, syscall_id);
    return 0;
}
```

Compile it with `clang`:

```bash
clang -O2 -g -target bpf -c src/bpf/programs.c -o src/bpf/programs.o
```

---

## Writing the Rust Userspace Program

In `src/main.rs`:

```rust
use aya::{Bpf, programs::TracePoint};
use tokio::signal;

#[tokio::main]
async fn main() -> Result<(), anyhow::Error> {
    let mut bpf = Bpf::load_file("src/bpf/programs.o")?;
    let program: &mut TracePoint = bpf.program_mut("trace_sys_enter").unwrap().try_into()?;
    program.load()?;
    program.attach("syscalls", "sys_enter")?;

    println!("Running eBPF strace... Press Ctrl+C to exit.");
    signal::ctrl_c().await?;
    println!("Exiting.");

    Ok(())
}
```

---

## Running the Tool

1. Ensure the kernel supports eBPF:

```bash
uname -r
bpftool feature probe
```

2. Run the program with elevated privileges:

```bash
sudo cargo run
```

Output example:

```
Running eBPF strace... Press Ctrl+C to exit.
PID 12345 called syscall ID 5
PID 12345 called syscall ID 12
```

---

## Conclusion

This project demonstrates how eBPF and Rust can be combined to build an efficient `strace`-like tool. With more advanced filtering and context capturing, this tool can become a powerful asset for system profiling and debugging.

For further exploration, consider adding support for syscall names, argument inspection, and process filtering.

Happy tracing!
