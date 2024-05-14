[TNAME]:incompleter

# incompleter

## Overview

This README provides guidance for setting up and running incompleter with case studies from youtube-dl. The setup involves cloning repositories and preparing environments to reproduce and study various bugs.

### CASE STUDY: YOUTUBE-DL

#### Bug Occurrence Table:
| Bug Number | Count |
|------------|-------|
| 1          | 1     |
| 2          | 2     |
| 4          | 1     |
| 9          | 2     |
| 19         | 3     |
| 20         | 1     |
| 22         | 2     |
| 24         | 2     |
| 28         | 1     |

### Setup Repositories

Clone and setup the following repositories:
- BugsInPy: [https://github.com/soarsmu/BugsInPy/tree/master](https://github.com/soarsmu/BugsInPy/tree/master)
- LExecutor: [https://github.com/michaelpradel/LExecutor/tree/main](https://github.com/michaelpradel/LExecutor/tree/main)

Additionally, clone this repository to your local system:
```bash
git clone [repository_url]
cd [repository_directory]
```

Ensure Python 3.11 is installed and set up on your machine, then install the required dependencies:
```bash
pip install -r requirements.txt
```

Replace `[repository_url]` and `[repository_directory]` with the actual URL of the repository and the directory name where the repository should be cloned.

### Configure BugsInPy

After cloning and adding BugsInPy to your PATH:
1. Checkout the desired bug:
   ```bash
   bugsinpy-checkout -p youtube-dl -v 0 -i [bug_number] -w [path/to/dir]
   ```
2. Navigate to the working directory and compile:
   ```bash
   cd [path/to/dir/youtube-dl]
   bugsinpy-compile
   ```
3. Copy the relevant test file from the incompleter data:
   ```bash
   cp [incompleter/data/casestudy_data/bug[bug_number]_[trial_number].py] [path/to/dir/youtube-dl/test/]
   ```

### Setup LExecutor

After installing LExecutor in development mode (see `INSTALL.md` in their repository):
1. Start the model server:
   ```bash
   python3 -m lexecutor.predictors.codet5.ModelServer
   ```
2. Instrument the Python files:
   ```bash
   python3 -m lexecutor.Instrument --files [incompleter/data/casestudy_data/*.py]
   ```
3. Copy `iids.json` to the LExecutor directory and the youtube-dl directory within the bug directory:
   ```bash
   cp iids.json [path/to/dir/youtube-dl/ and path/to/dir/LExecutor/]
   ```

### Running Incompleter

Execute the incompleter script by specifying the directory and script:
```bash
python3 -m main.main [path/to/dir/youtube-dl/] -s test/[bug_script].orig -c --bugs
```

### Example Execution

#### Prepare the Environment
```bash
bugsinpy-checkout -p youtube-dl -v 0 -i 19 -w [home/anon/anon/git/BugsInPy/framework/bin/youtube-dl-bugs/bug19]
```

```
cd [home/anon/anon/git/BugsInPy/framework/bin/youtube-dl-bugs/bug19/youtube-dl/]
```

```
bugsinpy-compile
```

```
python3 -m lexecutor.Instrument --files [mnt/c/Users/anon/git/incompleter/data/casestudy_data/*.py]
```
```
cp iids.json [LExecutor directory and youtube-dl directory]
```

#### Copy Necessary Scripts
```bash
cp [bug19_2.py and bug19_2.py.orig] [home/anon/anon/git/BugsInPy/framework/bin/youtube-dl-bugs/bug19/youtube-dl/test/]
```

#### Run the Models
```bash
# In a separate terminal
python3 -m lexecutor.predictors.codet5.ModelServer

# Back in the main terminal
cd [home/anon/anon/git/BugsInPy/framework/bin/youtube-dl-bugs/bug19/youtube-dl/]
python3 test/bug19_2.py  # For LExecutor

cd [home/anon/anon/git/incompleter/src/]
python3 -m main.main [path/to/dir] -s test/bug19_2.py.orig -c --bugs  # For Incompleter
```

### Note
Runtime may vary; some bugs might take 20 or more minutes to complete on certain machines.
```
