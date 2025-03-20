# Gametime Project Setup on Linux and macOS

Welcome to the setup guide for the Gametime project! This document provides instructions for setting up and running the Gametime project on both Linux and macOS. Follow the steps below to install the required dependencies and configure your environment for development and testing.

---

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

### 4. Compiling Local Passes

From the project root directory run:

```bash
clang++ -shared -fPIC src/custom_passes/custom_inline_pass.cpp -o src/custom_passes/custom_inline_pass.so `llvm-config --cxxflags --ldflags --libs` -Wl,-rpath,$(llvm-config --libdir)
```

---

## Running Tests

Once the setup is complete, you can run tests within the Gametime environment. Follow these steps to configure and execute your tests:

### 1. Configure the YAML File

Each test requires a YAML configuration file. Ensure that your YAML file is correctly set up with all the necessary test configurations.

### 2. Create a Test Class

Navigate to the `wcet_test.py` file and create a new test class based on one of the available backend configurations. Specify the path to your YAML configuration file in the `config_path` attribute.

#### Example:

```python
class TestBinarysearchARM(TestARMBackend):
    config_path = "./programs/binarysearch/config.yaml"
```

### 3. Add the Test Class to the Main Function

In the `main` function of `wcet_test.py`, add your newly created test class to the suite for execution.

#### Example:

```python
suite.addTests(loader.loadTestsFromTestCase(TestBinarysearchARM))
```

### 4. Run the Test

Run the test using the following command:

```bash
python wcet_test.py
```

---

## License

This project is licensed under the terms of the [MIT License](LICENSE).

---

## Contact

If you have any questions or encounter any issues, please open an issue on the GitHub repository or reach out to the project maintainers.

---

By following these instructions, you should be able to get Gametime up and running on your machine. Happy coding!
