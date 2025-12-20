import re
import os


def find_labels(bitcode_string, output_dir):
    """
    Extract labels from bitcode string representation of Path.

    Parameters:
        filename : str
            A file containing all of the basic block labels of the path to be analyzed,
            which is generated before running the SMT solver
    Returns:
        List[String]
            A List of basic block labels
    """

    # Use regular expression to find the labels
    labels = re.findall(r"%(\d+):", bitcode_string)
    # Convert labels to integers and store them in a list
    i = 0
    while True:
        filename = os.path.join(output_dir, f"labels_{i}.txt")
        try:
            with open(filename, "x") as f:
                for label in labels:
                    f.write(f"{label}\n")
            break
        except FileExistsError:
            i += 1

    return filename
