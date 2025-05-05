# Todo CLI

A simple command-line todo list manager for your Fish shell and WSL setup. The script (`todo.py`) and the data file (`todo.csv`) live together in the same directory.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Usage](#usage)
   - [Listing Tasks](#listing-tasks)
   - [Adding a Task](#adding-a-task)
   - [Removing a Task](#removing-a-task)
   - [Marking a Task Done](#marking-a-task-done)
5. [File Formats](#file-formats)
6. [Examples](#examples)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Python 3 installed in WSL
- Fish shell as your default shell
- WSL has access to your Windows filesystem (e.g., `/mnt/c/Users/<YourWinUser>/Documents`)

---

## Installation

1. **Place the files**

   ```bash
   # Create a folder if needed
   mkdir -p /mnt/c/Users/<YourWinUser>/Documents/todo

   # Copy or create the script and data
   cp todo.py /mnt/c/Users/<YourWinUser>/Documents/todo/todo.py
   touch /mnt/c/Users/<YourWinUser>/Documents/todo/todo.csv
   ```

2. **Make the script executable**

   ```bash
   chmod +x /mnt/c/Users/<YourWinUser>/Documents/todo/todo.py
   ```

3. **Initialize your CSV** (optional)
   ```bash
   cat > /mnt/c/Users/<YourWinUser>/Documents/todo/todo.csv << 'EOF'
   study for audiology exam,monday,done
   fleshout toolbox for final deliverable,monday,done
   411 case study pre submission,tuesday,done
   470 programming & non-programming hw,tues/wed/thurs,
   330 Individual mission concept,today,
   EOF
   ```

---

## Configuration

Add an alias in your Fish config (`~/.config/fish/config.fish`):

```fish
alias todo '/mnt/c/Users/<YourWinUser>/Documents/todo/todo.py'
```

Reload Fish to apply:

```bash
exec fish
```

---

## Usage

The `todo` command supports four actions:

### Listing Tasks

```bash
todo
```

Prints your tasks grouped into sections:

```
this week
[past]
- ...
[today]
- ...
[later]
- ...
```

### Adding a Task

```bash
todo add "<description>" <due-day>
```

- `<description>`: Task text (in quotes if it contains spaces)
- `<due-day>`: e.g. `monday`, `tues/wed`, `today`, `tomorrow`

**Example**:

```bash
todo add "prepare slides" friday
```

### Removing a Task

```bash
todo rm <index>
```

Removes the _N<sup>th</sup>_ task in the current list (1-based).

**Example**:

```bash
todo rm 3
```

### Marking a Task Done

```bash
todo done <index>
```

Marks the _N<sup>th</sup>_ task as `[done]`.

**Example**:

```bash
todo done 1
```

---

## File Formats

- **`todo.py`**: The main Python script. Must be executable and include the `#!/usr/bin/env python3` shebang.
- **`todo.csv`**: A comma-separated file with lines in the format:
  ```csv
  description,due,status
  ```
  - `description`: Task text
  - `due`: Day(s) (e.g. `monday`, `tues/wed`, `today`)
  - `status`: Leave empty or use `done`

---

## Examples

1. **List tasks**
   ```bash
   todo
   ```
2. **Add**
   ```bash
   todo add "email client" tuesday
   ```
3. **Remove**
   ```bash
   todo rm 2
   ```
4. **Done**
   ```bash
   todo done 4
   ```

---

## Troubleshooting

- **Permission denied**: Ensure you ran `chmod +x todo.py`.
- **Invalid index**: Check the list output to confirm the number.
- **Script not found**: Verify your alias path matches the script location.

---

_Enjoy staying organized!_
