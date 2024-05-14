import os
import glob

# Restores the files back to how it originally was.
# Removes and overwrites the lexecutor added logic
def rename_files():
    files = glob.glob('*.py.orig')
    
    for file in files:
        new_name = file.replace('.py.orig', '.py')
        if os.path.exists(new_name):
            os.remove(new_name)
        os.rename(file, new_name)
        print(f"Renamed '{file}' to '{new_name}'")

# Execute the function
if __name__ == "__main__":
    rename_files()
