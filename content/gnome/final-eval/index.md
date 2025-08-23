---
title: Sysprof GSoC Final Report
date: 2025-08-18
author: Varun R Mallya
description: Talks about my contribution process, project and how I worked on it
tags:
  - GSoC
  - GNOME
  - sysprof
  - eBPF
toc: off
---

We have finally reached the last week of GSoC 2025. It has been an amazing journey so far and I hope I'll be able to contribute more to GNOME in the coming future. Let summarise what I've done over the past few months and I'll also link to a few blogs explaining parts of this that are too long to fit here.

# Introduction
This summer, I had the opportunity to work on GNOME's Sysprof, a full system profiling tool. I was tasked with adding eBPF capabilities to Sysprof allowing it to be even more powerful than it already is. As discussed with my mentor Christian Hergert (@hergertme on gitlab.gnome.org), the project was transistioned from being just a project to reduce overhead of `/proc` file access to a bigger goal of allowing more eBPF programs to be added to Sysprof in general.  

This was accomplished by carefully designing the structure of the `sysprof-ebpf` binary with a few extensions planned for the future.  
Currently, Sysprof eBPF has capabilities to track CPU-usage, per interface network usage and can profile the cache as well. There is also a module written for getting per-process syscall usage for getting per-process syscall usage. But, ingesting data from this has proven to be quite a challenge for me. Also, we have better plans for this module in the coming future. 

# An overview of eBPF 
eBPF is a virtual machine present in the Linux kernel that allows tracing all functions that have not been inlined in the kernel. It allows adding a select number of data structures predefined in the standard and also ring buffers that allow buffering data into the userspace form the kernel just like proc allows for. eBPF is also pretty useful in the networking space. XDP and TC absed eBPF programs can help process packets much faster by sometimes offloading programs to the network card itself. It's a huge thing in the container networking space now too! Check out (Cilium)[https://github.com/cilium/cilium]. eBPF is also being extensively used in observability and profiling software as well (In fact some projects provide a lot of what Sysprof does just using eBPF based programs!). For now, you thank think of eBPF as a verified and restricted kernel module that is very portable across Kernel versions (if written right).

# The `sysprof-ebpf` module
