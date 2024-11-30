import subprocess
import sys

def run(command, shell=False):
    print(f"==> Executing command: {' '.join(command)}")
    result = subprocess.run(command, shell, check=True)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    return result.stdout