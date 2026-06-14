# Guardog 🐕‍🦺
**A Zero-Copy, High-Throughput PII Redaction Engine for Python**

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/Python-3.x-yellow.svg)](https://python.org)
[![C-Extension](https://img.shields.io/badge/C--Core-Optimized-red.svg)]()

Guardog is a highly optimized C-extension for Python designed to bypass the Global Interpreter Lock (GIL) and mutate gigabyte-scale memory buffers in place. 

It was built by **CyBurn Digital** to solve a critical infrastructure bottleneck: Python's standard `re` (regex) module duplicating massive strings in RAM during data ingestion, leading to out-of-memory (OOM) server crashes.

By leveraging the Python `w*` buffer protocol and a compiled Deterministic Finite Automaton (DFA) matrix, Guardog achieves true zero-copy mutation with zero memory overhead.

---

## 📊 The Benchmark: 1GB in 1.1 Seconds

We tested Guardog against Python's highly optimized, native C-backed `re` module using a 1 Gigabyte raw text payload containing thousands of embedded secrets. 





**The Results:**
*   **Standard Regex:** 25.54 seconds | **947.6 MiB** Memory Overhead
*   **Guardog Engine:** 1.13 seconds | **0.0 MiB** Memory Overhead (22x Faster)

![Memory Benchmark](
<img width="1260" height="540" alt="benchmark_results" src="https://github.com/user-attachments/assets/d48b9b4e-961d-4c14-88ef-a165215cfd9e" />
> *The massive mountain is Python's standard regex struggling and duplicating data. The tiny, perfectly flat line at the bottom right (26s mark) is Guardog chewing through the same 1GB file in 1 second without a single byte of memory overhead.*

---

## ⚡ Core Features

*   **True Zero-Copy Mutation:** Accepts mutable `bytearray` objects and overwrites PII directly in memory. No string allocation, no data duplication.
*   **GIL Bypass:** Releases the Python Global Interpreter Lock entirely, allowing your main application to continue running asynchronously.
*   **DFA Matrix Execution:** Scans using a pre-compiled, mathematically deterministic state machine (`guardog.matrix`) rather than backtracking regex, ensuring $O(N)$ guaranteed execution time regardless of payload complexity.
*   **Multi-Threading (OpenMP):** Automatically detects payload size. For payloads over 5MB, it spins up parallel C-threads to chunk and sanitize the buffer simultaneously.

---

## 🛠️ Installation

Guardog requires a C compiler to build the native extension. 

1. Clone the repository:
```bash
   git clone [https://github.com/thedevilhimselfcodes/guardog.git](https://github.com/thedevilhimselfcodes/guardog.git)
   cd guardog
   
```
   
## Build and install the C-extension:

Bash
```
python setup.py build_ext --inplace

```
Ensure guardog.matrix and guardog_meta.json are in your working directory.

## 🚀 Usage
Guardog features a clean, Pythonic wrapper that automatically handles the zero-copy logic.

Python
```from guardog import GuardogSession

# Initialize the engine (loads the DFA matrix)
session = GuardogSession()

# 1. Load your massive payload as raw bytes
with open("massive_server_logs.log", "rb") as f:
    raw_bytes = f.read()

# 2. Create a mutable buffer
mutable_buffer = bytearray(raw_bytes)

# 3. Execute Zero-Copy Sanitize
result = session.sanitize(mutable_buffer)

print(f"Redaction complete. Total secrets found: {len(result['matches'])}")
```
## ⚖️ License & Commercial Use (Dual-License)
Guardog is open-source and released under the GNU General Public License v3.0 (GPLv3). You are free to use, modify, and distribute this software, provided that any derivative works or backend systems incorporating it are also strictly open-sourced under the GPLv3.

## 🏢 Enterprise Commercial License
For enterprise compliance, most corporations cannot open-source their proprietary backend infrastructure. If you wish to embed Guardog into a closed-source commercial product, SaaS backend, or internal corporate data pipeline, you must acquire a Commercial License.

For commercial licensing, custom DFA matrix training, and enterprise implementation consulting, contact the maintainers at mailtovindana@gmail.com.
