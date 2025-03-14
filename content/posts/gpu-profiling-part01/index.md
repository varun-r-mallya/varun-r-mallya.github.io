---
title: Exploring Mesa Utils to acquire GPU statistics Part 1
date: 2025-03-14
author: Varun R Mallya
description: exploring GPU statistics Part 01
tags:
  - GPUs
  - Mesa
  - sysprof
---

## Introduction
I am trying to find ways to add a GPU profiling feature to [Sysprof](https://gitlab.gnome.org/GNOME/sysprof), a GNOME developer utility. Turns out, the people over at Mesa just merged a [new feature](https://gitlab.freedesktop.org/mesa/mesa/-/merge_requests/33814#13dca6a6550094ec5f50dc7542168c029cae252b) from which I can export out shader statistics and GPU statistics as well. I am going to be describing the method in which I found these measurable statistics and I'll explain what they do as well. This blog is the first one in a series of blogs that I'll be writing about this topic.

## Steps to aquire the header file
The first step is to clone the Mesa repository. You can do this by running the following command:
```bash
git clone https://gitlab.freedesktop.org/mesa/mesa.git
```
Once you have cloned the repository, you can navigate to the `src/util` directory. Here, you can find the 'src/util/process_shader_stats.py' file. Create a virtual environment and install the required dependencies by running the following commands:
```bash
python3 -m venv venv
source venv/bin/activate
pip install mako textwrap xml
```
Now, you can run the script by running the following command:
```bash
python3 process_shader_stats.py
```
This will generate the 'src/util/shader_stats.h' file which contains all the statistics that you can measure.

## The statistics themselves and their relavance to `sysprof` and profiling
I'll be posting individually about each architecture and each statistic in that architecture in the coming week. For now, I've just checked out the `adreno` architecture. This is used on Qualcomm GPUs and was the most most detailed one I could find.

### Adreno Shader Statistics

##### Max Waves Per Core
- The maximum number of simultaneous waves (groups of threads) that can run on a single core.
- Higher values indicate better utilization of the GPU's parallel processing, but too many waves can lead to blocking of operations and contention for resources.

##### Instruction Count
- The total number of IR3 (Intermediate Representation 3) instructions in the final shader executable.
- A higher instruction count may indicate a more complex shader, which could impact performance.
- IR3 is basically just a representation of the shader program before it actually gets munched down by the proprietory drivers into GPU specific instructions. 
- More about it [here](https://docs.mesa3d.org/drivers/freedreno/ir3-notes.html)

##### Code Size
- The total size of the shader executable in dwords (32-bit units).
- Larger code sizes may consume more memory and could affect caching efficiency.

##### NOPs Count
- The number of No-Operation (NOP) instructions in the shader.
- NOPs are placeholders or padding instructions. Too many NOPs can indicate inefficiencies in the shader code.

##### MOV Count
- The number of MOV (move) instructions in the shader.
- MOV instructions are used to copy data between registers. Excessive MOVs can indicate suboptimal register usage or unnecessary data movement.

##### COV Count
- The number of COV (coverage) instructions in the shader.
- COV instructions are related to handling pixel coverage in fragment shaders. A high count may indicate complex pixel processing.

##### Registers Used
- The total number of full registers used by the shader.
- Register usage impacts resource allocation on the GPU. High register usage can limit the number of concurrent waves.

##### Half-Registers Used
- The number of half-registers (16-bit registers) used by the shader.
- Half-registers are used for smaller data types. Efficient use of half-registers can save resources.

##### Last Interpolation Instruction
- The instruction where varying storage in Local Memory is released.
- This indicates the point in the shader where interpolation (e.g., for vertex attributes) is no longer needed, freeing up resources.

##### Last Helper Instruction
- The instruction where helper invocations (extra threads used for derivatives or texture filtering) are killed.
- Helper invocations consume resources, so ending them early can improve performance.

#### Synchronization and Stalling

##### Instructions with SS Sync Bit
- The number of instructions with the SS (Shader Shader) sync bit set. This bit prevents Read-After-Write (RAW) hazards for long-latency instructions.
- SS syncs ensure correctness but can introduce stalls, impacting performance.

##### Instructions with SY Sync Bit
- The number of instructions with the SY (Shader Memory) sync bit set. This bit prevents RAW hazards for memory load operations.
- SY syncs ensure memory operations are correctly ordered but can also cause stalls.

##### Estimated Cycles Stalled on SS
- The estimated number of cycles the shader stalls due to SS syncs.
- This provides a better metric for understanding the performance impact of SS syncs.

##### Estimated Cycles Stalled on SY
- The estimated number of cycles the shader stalls due to SY syncs.
- This helps quantify the performance impact of memory-related stalls.

#### Instruction Categories

##### `cat0` to `cat7` Instructions
- The number of instructions in each category (cat0 to cat7). These categories represent different types of instructions (e.g., arithmetic, memory, control flow).
- Understanding the distribution of instruction types can help identify bottlenecks or inefficiencies in the shader.

##### Private Memory Access

###### STP Count
- The number of STore Private (STP) instructions, which store data to private memory.
- Private memory accesses can be slower than register accesses, so minimizing STPs can improve performance.

##### LDP Count
- The number of LoaD Private (LDP) instructions, which load data from private memory.
- Similar to STPs, excessive LDPs can indicate inefficient memory usage.

##### Preamble Statistics
##### Preamble Instruction Count
- The number of IR3 instructions in the preamble (a setup phase before the main shader execution).
- A large preamble can increase shader launch overhead.

##### Early Preamble
- Whether the preamble is executed early (before the main shader).
- Early preamble execution can reduce latency by overlapping setup with other work.


## What I understood from this
These are pretty detailed honestly and I have no idea which ones can be used to profile programs. I tried to Google and understand each of these but I'm probably still missing a lot of stuff. Expect a lot more analysis in the coming weeks. Also, what I originally wanted was GPU stats and not shader stats really, but I think profiling programs at the shader level is the actual way to go. This might be a better indicator of bottlenecks in the program

