import os
import re

# Regex to find invalid tailwind v4 color variable usage in components
# e.g., bg-[--color-card-bg], text-[--color-accent]/10, hover:border-[--color-accent]
# Groups: 
# 1: Prefix (e.g. bg, text, border, hover:bg)
# 2: Color name (e.g. card-bg, accent)
# 3: Opacity modifier if exists (e.g. /10, /50)
pattern = re.compile(r'([a-zA-Z0-9-:]+)-\[--color-([a-zA-Z0-9-]+)\](\/[0-9]+)?')

def process_file(file_path):
    print(f"Processing: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content, count = pattern.subn(r'\1-\2\3', content)

    if count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"  Fixed {count} instances.")
    else:
        print("  No instances found.")

def main():
    base_dir = r"c:\Users\avav\Documents\freqtrade\web"
    target_dirs = [
        os.path.join(base_dir, "pages"),
        os.path.join(base_dir, "src")
    ]

    for target_dir in target_dirs:
        if not os.path.exists(target_dir):
            print(f"Directory {target_dir} does not exist. Skipping.")
            continue
        
        for root, dirs, files in os.walk(target_dir):
            for file in files:
                if file.endswith(('.tsx', '.ts')):
                    file_path = os.path.join(root, file)
                    process_file(file_path)

if __name__ == "__main__":
    main()
