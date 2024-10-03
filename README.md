# Gametime Project Setup on Linux and macOS

This repository provides the setup instructions for running the Gametime project on both Linux and macOS. Follow the steps below to install the necessary dependencies and configure the project environment for your platform.

## Setup Instructions

### 1. Clone the Gametime Repository
Start by pulling the Gametime repository from GitHub:
```bash
git clone https://github.com/icyphy/gametime.git
cd gametime
git submodule update --init --recursive
```
### 2. Install LLVM and Clang (Version 13)

#### On Linux (Ubuntu/Debian):
To install version 13 of `clang` and `llvm`, use the following commands:

```bash
sudo apt update
sudo apt install clang-13 llvm-13
```

Ensure that version 13 of both tools is used by setting them as the default:
```bash
sudo update-alternatives --install /usr/bin/clang clang /usr/bin/clang-13 100
sudo update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-13 100
```

#### On macOS:
To install version 13 of `clang` and `llvm`, follow these steps:
1. Ensure that Homebrew is installed.
2. Install `llvm` version 13:
   ```bash
   brew install llvm@13
   ```

3. Ensure that version 13 is correctly configured in your `PATH`:
   ```bash
   export PATH="/usr/local/opt/llvm@13/bin:$PATH"
   ```


### 3. Install Extra Dependencies and Local Modules

Install the Python dependencies and additional required libraries:

```bash
pip install -e .
pip install -r requirements.txt
```

Make sure that the `pycparser` directory is in the same location as your Gametime directory so that it can find the necessary stubs.

#### On Linux (Ubuntu/Debian):
Install additional required libraries:
```bash
sudo apt-get install graphviz libgraphviz-dev
```

#### On macOS:
Install additional required libraries using Homebrew:
```bash
brew install graphviz
```

### 4. Install KLEE

#### KLEE Installation
For KLEE installation instructions, visit the [KLEE official website](https://klee.github.io/).

## License
This project is licensed under the terms of the [MIT License](LICENSE).

## Contact
If you have any questions or issues, please open an issue on the GitHub repository or contact the project maintainers.
