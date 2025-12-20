# Gametime Project Setup on Linux and macOS

Welcome to the setup guide for the Gametime project! This document provides instructions for setting up and running the Gametime project on both Linux and macOS. Follow the steps below to install the required dependencies and configure your environment for development and testing.


## Setup Instructions

### 1. Clone the Gametime Repository

Begin by cloning the Gametime repository from GitHub and initializing the submodules:

```bash
git clone https://github.com/icyphy/gametime.git
cd gametime
git submodule update --init --recursive
```

### 2. Install LLVM and Clang (Version 16)

Gametime requires LLVM and Clang version 16. The installation instructions differ slightly between Linux and macOS:

#### On Linux (Ubuntu/Debian):
Update your package manager and install LLVM and Clang version 13:

```bash
sudo apt update
sudo apt install clang-16 llvm-16
```

Ensure that version 16 is used by setting it as the default:

```bash
sudo update-alternatives --install /usr/bin/clang clang /usr/bin/clang-16 100
sudo update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-16 100
```

#### On macOS:
First, ensure that Homebrew is installed, then install LLVM version 16 using the following commands:

```bash
brew install llvm@16
```

After installation, find out the installation path for llvm@16:

```bash
brew info llvm@16
```

brew will then return an output along the lines of 
```
$ brew info llvm@16
==> llvm@16: stable 16.0.6 (bottled) [keg-only]
Next-gen compiler infrastructure
https://llvm.org/
Installed
/usr/local/Cellar/llvm@16/16.0.6_1 (<== copy this)
```

Update your `PATH` to include LLVM version 16:

```bash
export PATH="/usr/local/Cellar/llvm@16/16.0.6_1/bin:$PATH"
```

### 3. Install Extra Dependencies and Local Modules

#### On Linux (Ubuntu/Debian):
Install additional system libraries:

```bash
sudo apt-get install graphviz libgraphviz-dev
```

#### On macOS:
Install the additional libraries via Homebrew:

```bash
brew install graphviz
```

#### Install Python dependencies:

Install the required Python packages and additional system libraries:

```bash
pip install -e .
pip install -r requirements.txt
```

If you are having trouble installing pygraphviz on macOS try the following: [StackOverflow](https://stackoverflow.com/questions/69970147/how-do-i-resolve-the-pygraphviz-error-on-mac-os)

### 4. Install KLEE

To use KLEE with Gametime, follow the installation instructions on the [KLEE official website](https://klee.github.io/).

### 5. Install the FlexPRET Emulator (Recommended)

To use the FlexPRET emulator with GameTime, follow the installation instructions on the [FlexPRET Github Page](https://github.com/pretis/flexpret).

### 6. Configure Environment Variables

After installing KLEE and FlexPRET, you need to set up environment variables so GameTime can find these dependencies. Create or edit the `env.bash` file in the GameTime project root:

```bash
# Add KLEE include path
export C_INCLUDE_PATH="<path_to_klee>/include:$C_INCLUDE_PATH"

# Source FlexPRET environment (sets up PATH and other variables)
source <path_to_flexpret>/env.bash
```

**Example `env.bash` file:**

```bash
# KLEE headers
export C_INCLUDE_PATH=/opt/homebrew/Cellar/klee/3.1_4/include:$C_INCLUDE_PATH

# FlexPRET environment (includes fp-emu in PATH)
source /Users/username/Documents/projects/flexpret/env.bash
```

**Note:** Replace the paths with your actual installation locations. The FlexPRET `env.bash` file typically adds the emulator (`fp-emu`) to your `PATH` automatically.

You'll need to source this file before using GameTime:

```bash
source env.bash
```

### 7. Compile LLVM Passes

From the project root directory run:

```bash
clang++ -shared -fPIC src/custom_passes/custom_inline_pass.cpp -o src/custom_passes/custom_inline_pass.so `llvm-config --cxxflags --ldflags --libs` -Wl,-rpath,$(llvm-config --libdir)
```

## Using GameTime

Once the setup is complete, you can use GameTime to analyze the worst-case execution time (WCET) of your C programs.

### Command Line Interface

GameTime provides a command-line interface for easy WCET analysis:

```bash
gametime <path_to_folder_or_config_file> [options]
```

**Options:**
- `-b, --backend {flexpret,x86,arm}` - Choose execution backend (required if not in config)
- `--no-clean` - Keep temporary files for debugging
- `-h, --help` - Show help message

**Note:** Make sure to source the environment file before running gametime:

```bash
source env.bash
```

### Preparing a Test Case

To analyze a C program with GameTime, you need:

1. **A C source file** containing the function you want to analyze
2. **A configuration file** (`config.yaml`) in the same directory

#### Configuration File Template

Create a `config.yaml` file in your program's directory:

```yaml
---
gametime-project:
  file:
    location: your_program.c              # Your C source file
    analysis-function: function_to_analyze # Function name to analyze
    additional-files: [helper.c]          # Optional: additional source files
    start-label: null                     # Optional: start analysis at label
    end-label: null                       # Optional: end analysis at label

  preprocess:
    include: null                         # Optional: directories with headers
    merge: null                           # Optional: files to merge
    inline: yes                           # Inline function calls (recommended)
    unroll-loops: yes                     # Unroll loops (recommended)

  analysis:
    maximum-error-scale-factor: 10
    determinant-threshold: 0.001
    max-infeasible-paths: 100
    ilp-solver: glpk                      # ILP solver to use
    backend: flexpret                     # Backend: flexpret, x86, or arm
```

#### Example: Simple C Program

Create a directory with your program and config:

```
my_program/
├── example.c
└── config.yaml
```

**example.c:**
```c
int compute(int x) {
    if (x > 10) {
        return x * 2;
    } else if (x > 5) {
        return x + 10;
    } else {
        return x;
    }
}
```

**config.yaml:**
```yaml
---
gametime-project:
  file:
    location: example.c
    analysis-function: compute
    
  preprocess:
    inline: yes
    unroll-loops: yes
    
  analysis:
    ilp-solver: glpk
    backend: flexpret
```

### Running Analysis

After preparing your test case, run the analysis:

```bash
# Make sure to source the environment first
source env.bash

# Run analysis
gametime my_program --backend flexpret
```

### Understanding the Output

GameTime will display:

1. **Preprocessing progress**: Compilation, inlining, loop unrolling
2. **DAG generation**: Control flow graph construction  
3. **Basis paths**: Initial set of representative paths
4. **Path generation**: Additional paths discovered
5. **Measurements**: Execution time for each path
6. **Final results**: WCET and the worst-case path

Example output:

```
============================================================
GAMETIME ANALYSIS RESULTS
============================================================
Function analyzed: test
Backend: flexpret
Number of basis paths: 5
Number of generated paths: 6

Basis Paths:
  0: gen-basis-path-row0-attempt0 = 62
  1: gen-basis-path-row1-attempt1 = 62
  2: gen-basis-path-row2-attempt2 = 50
  3: gen-basis-path-row3-attempt4 = 50
  4: gen-basis-path-row4-attempt6 = 44

Generated Paths:
  0: feasible-path0 = predicted: 62.0, measured: 62 *WCET*
  1: feasible-path1 = predicted: 62.0, measured: 62 *WCET*
  2: feasible-path2 = predicted: 50.0, measured: 50
  3: feasible-path3 = predicted: 50.0, measured: 50
  4: feasible-path4 = predicted: 44.0, measured: 45
  5: feasible-path5 = predicted: 44.0, measured: 44

Worst-Case Execution Time (WCET): 62
WCET Path: feasible-path0
============================================================

Analysis completed successfully!
```

### Available Backends

- **flexpret**: Uses the FlexPRET RISC-V emulator for precise timing measurements (recommended for embedded systems)
- **x86**: Uses the x86 host machine for timing measurements
- **arm**: Uses the ARM host machine for timing measurements

### Example Commands

```bash
# Analyze with FlexPRET backend
gametime test/if_statements --backend flexpret

# Keep temporary files for debugging
gametime test/if_statements --backend flexpret --no-clean

# Specify config file directly
gametime test/if_statements/config.yaml --backend flexpret
```

### Exploring Example Programs

GameTime includes several example programs in the `test` directory:

```bash
# List available examples
ls test/

# Run an example
gametime test/if_statements --backend flexpret
```


## License

This project is licensed under the terms of the [MIT License](LICENSE).


## Contact

If you have any questions or encounter any issues, please open an issue on the GitHub repository.

