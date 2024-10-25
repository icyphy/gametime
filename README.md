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

### 2. Install LLVM and Clang (Version 13)

Gametime requires LLVM and Clang version 13. The installation instructions differ slightly between Linux and macOS:

#### On Linux (Ubuntu/Debian):
Update your package manager and install LLVM and Clang version 13:

```bash
sudo apt update
sudo apt install clang-13 llvm-13
```

Ensure that version 13 is used by setting it as the default:

```bash
sudo update-alternatives --install /usr/bin/clang clang /usr/bin/clang-13 100
sudo update-alternatives --install /usr/bin/llvm-config llvm-config /usr/bin/llvm-config-13 100
```

#### On macOS:
First, ensure that Homebrew is installed, then install LLVM version 13 using the following commands:

```bash
brew install llvm@13
```

After installation, update your `PATH` to include LLVM version 13:

```bash
export PATH="/usr/local/opt/llvm@13/bin:$PATH"
```

### 3. Install Extra Dependencies and Local Modules

Install the required Python packages and additional system libraries:

```bash
pip install -e .
pip install -r requirements.txt
```

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

### 4. Install KLEE

To use KLEE with Gametime, follow the installation instructions on the [KLEE official website](https://klee.github.io/).

---

## Running Tests

Once the setup is complete, you can run tests within the Gametime environment. Follow these steps to configure and execute your tests:

### 1. Configure the YAML File

Each test requires a YAML configuration file. Ensure that your YAML file is correctly set up with all the necessary test configurations.

### 2. Create a Test Class

Navigate to the `wcet.py` file and create a new test class based on one of the available backend configurations. Specify the path to your YAML configuration file in the `config_path` attribute.

#### Example:

```python
class TestBinarysearchARM(TestARMBackend):
    config_path = "./programs/binarysearch/config.yaml"
```

### 3. Add the Test Class to the Main Function

In the `main` function of `wcet.py`, add your newly created test class to the suite for execution.

#### Example:

```python
suite.addTests(loader.loadTestsFromTestCase(TestBinarysearchARM))
```

### 4. Run the Test

Run the test using the following command:

```bash
python wcet.py
```

---

## License

This project is licensed under the terms of the [MIT License](LICENSE).

---

## Contact

If you have any questions or encounter any issues, please open an issue on the GitHub repository or reach out to the project maintainers.

---

By following these instructions, you should be able to get Gametime up and running on your machine. Happy coding!