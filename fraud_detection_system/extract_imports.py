import os
import re


def extract_imports_from_file(file_path):
    imports = []

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()

                # Match "import xyz"
                if line.startswith("import "):
                    imports.append(line)

                # Match "from xyz import abc"
                elif line.startswith("from "):
                    imports.append(line)

    except Exception as e:
        print(f"Skipping {file_path}: {e}")

    return imports


def scan_directory(root_dir):
    all_imports = []

    for foldername, _, filenames in os.walk(root_dir):
        for filename in filenames:
            if filename.endswith(".py"):
                file_path = os.path.join(foldername, filename)
                file_imports = extract_imports_from_file(file_path)
                all_imports.extend(file_imports)

    return all_imports


def save_imports(imports, output_file="all_imports.txt"):
    # remove duplicates while keeping order
    seen = set()
    unique_imports = []

    for imp in imports:
        if imp not in seen:
            seen.add(imp)
            unique_imports.append(imp)

    with open(output_file, "w", encoding="utf-8") as f:
        for imp in unique_imports:
            f.write(imp + "\n")

    print(f"\nSaved {len(unique_imports)} imports to {output_file}")


if __name__ == "__main__":
    root_dir = "."

    print(f"Scanning directory: {os.path.abspath(root_dir)}")
    imports = scan_directory(root_dir)
    save_imports(imports)
