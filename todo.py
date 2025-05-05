#!/usr/bin/env python3
import os, csv, re, argparse, sys, calendar
from datetime import datetime, timedelta, date
import shutil

# ─── Configuration ─────────────────────────────────────────────────────────────

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
TODO_FILE  = os.path.join(SCRIPT_DIR, "todo.csv")

# ANSI color codes
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"

RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"


# map common day names to weekday indices
day_map = {
    'monday':0,'mon':0,
    'tuesday':1,'tue':1,'tues':1,
    'wednesday':2,'wed':2,
    'thursday':3,'thu':3,'thur':3,'thurs':3,
    'friday':4,'fri':4,
    'saturday':5,'sat':5,
    'sunday':6,'sun':6,
}

# map month names/abbrevs to month numbers
month_map = {}
for i in range(1,13):
    month_map[calendar.month_name[i].lower()]   = i
    month_map[calendar.month_abbr[i].lower()]   = i

# today/tomorrow date and weekday index
_now        = datetime.now()
today_date  = _now.date()
today_idx   = _now.weekday()
tomorrow_date = today_date + timedelta(days=1)
# ─── Backup & Undo Helpers ────────────────────────────────────────────────────────────

def backup_tasks():
    """Copy current TODO_FILE → TODO_FILE.bak before mutating."""
    if os.path.exists(TODO_FILE):
        shutil.copy2(TODO_FILE, TODO_FILE + '.bak')

def undo_last():
    """Restore the last backup if it exists."""
    bak = TODO_FILE + '.bak'
    if os.path.exists(bak):
        shutil.copy2(bak, TODO_FILE)
        print("Undid last change.")
    else:
        print("Nothing to undo.", file=sys.stderr)
        sys.exit(1)


# ─── Parsing Helpers ────────────────────────────────────────────────────────────

def parse_due_info(text):
    """
    Return (weekday_indices, due_date_or_None).
    - If text is month+day (e.g. 'may7'), returns its actual date.
    - Else if text is 'today'/'tomorrow' or a weekday, returns indices.
    """
    t = text.strip().lower()

    # 1) month-day format?
    m = re.match(r'^([a-zA-Z]+)(\d{1,2})$', t)
    if m:
        mon, day = m.group(1).lower(), int(m.group(2))
        if mon in month_map:
            yr = today_date.year
            try:
                due = date(yr, month_map[mon], day)
            except ValueError:
                due = date(yr, month_map[mon], day)  # will error if invalid
            return [due.weekday()], due

    # 2) today / tomorrow
    if t in ('today','tod'):
        return [today_idx], None
    if t in ('tomorrow','tom'):
        return [(today_idx + 1) % 7], None

    # 3) weekday or list of them
    parts = re.split(r'[\/,]', t)
    idxs = []
    for p in parts:
        key = p.strip().lower()
        if key in day_map:
            idxs.append(day_map[key])
    return idxs, None

def group_task(indices):
    """Decide section based on weekday indices."""
    if today_idx in indices: 
        return 'today'
    if all(d < today_idx for d in indices):
        return 'past'
    return 'later'

# ─── Task I/O ──────────────────────────────────────────────────────────────────

def load_tasks():
    tasks = []
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, newline='') as f:
            for row in csv.reader(f):
                if not row or row[0].startswith('#'):
                    continue
                desc = row[0]
                due  = row[1] if len(row)>1 else ''
                stat = row[2] if len(row)>2 else ''
                tasks.append((desc, due, stat))
    return tasks

def save_tasks(tasks):
    with open(TODO_FILE, 'w', newline='') as f:
        w = csv.writer(f)
        for desc,due,stat in tasks:
            w.writerow([desc, due, stat])

# ─── CRUD Operations ────────────────────────────────────────────────────────────

def add_task(desc, due):
    backup_tasks()
    ts = load_tasks()
    # if due is a bare weekday name (not month+day, today, or tomorrow),
    # convert it now into the next date and reformat as "monthday"
    weekday_name = due.strip().lower()
    if (re.fullmatch(r'[a-zA-Z]+', weekday_name)
    and weekday_name not in ('today','tod','tomorrow','tom')
    and weekday_name in day_map):
        
        target_idx = day_map[weekday_name]
        # how many days until that weekday (0 if today)
        delta = (target_idx - today_idx) % 7
        due_date = today_date + timedelta(days=delta)
        # rewrite due as e.g. "april29"
        due = due_date.strftime('%B').lower() + str(due_date.day)

    ts.append((desc, due, ''))
    save_tasks(ts)
    print(f"Added: {desc} ({due})")

def remove_task(idx):
    backup_tasks()
    ts = load_tasks()
    display = build_display_list(ts)
    try:
        orig_idx = display[idx-1]['orig_idx']
    except IndexError:
        print("✖ invalid index", file=sys.stderr)
        sys.exit(1)
    rem = ts.pop(orig_idx)
    save_tasks(ts)
    print(f"Removed: {rem[0]}")

def mark_done(idx):
    backup_tasks()
    ts = load_tasks()
    display = build_display_list(ts)
    try:
        orig_idx = display[idx-1]['orig_idx']
    except IndexError:
        print("✖ invalid index", file=sys.stderr)
        sys.exit(1)
    desc, due, _ = ts[orig_idx]
    ts[orig_idx] = (desc, due, 'done')
    save_tasks(ts)
    print(f"Marked done: {desc}")

def unmark_done(idx):
    backup_tasks()
    ts = load_tasks()
    display = build_display_list(ts)
    try:
        orig_idx = display[idx-1]['orig_idx']
    except IndexError:
        print("✖ invalid index", file=sys.stderr)
        sys.exit(1)
    desc, due, _ = ts[orig_idx]
    ts[orig_idx] = (desc, due, '')    # clear the status
    save_tasks(ts)
    print(f"Unmarked done: {desc}")


# ─── Listing & Formatting ───────────────────────────────────────────────────────

def list_tasks():
    """
    Build and display the todo list, grouped into [past], [today], [later],
    filtering past to the last 7 days, sorting descending by due date, and
    numbering entries for use with `todo done N`, `todo rm N`, etc.
    """
    display = build_display_list(load_tasks())

    header = f"--- Todo {today_date.strftime('%B %d, %Y')} ---"
    print(f"{BOLD}{CYAN}{header}{RESET}")
    print(f"{DIM}{'-' * len(header)}{RESET}")

    current_sec = None
    for n, task in enumerate(display, start=1):
        sec = task['section']
        # print section header once
        if sec != current_sec:
            print(f"{BOLD}{MAGENTA}[{sec}]{RESET}")
            current_sec = sec

        suf = f" [{task['stat']}]" if task['stat'] else ""
        # choose color
        if task['stat'] == 'done':
            color = DIM
        elif task['due'] == "Tomorrow":
            color = YELLOW
        elif sec == 'today':
            color = GREEN
        elif sec == 'later':
            color = BLUE
        else:
            color = RED
        print(f"{color}{n}. {task['desc']} ({task['due']}){suf}{RESET}")
    print()

def build_display_list(tasks):
    """
    Turn the raw `tasks = [(desc,due,stat),…]` into a flat list of dicts:
    - filtered exactly like list_tasks()
    - tagged with orig_idx so undo/done/rm can find the right CSV row
    - sorted descending by date within each section
    """
    buckets = {'past': [], 'today': [], 'later': []}
    for idx, (desc, due_raw, stat) in enumerate(tasks):
        idxs, due_date = parse_due_info(due_raw)
        if due_date:
            if due_date < today_date:
                section = 'past'
            elif due_date == today_date:
                section = 'today'
            else:
                section = 'later'
        else:
            section = group_task(idxs)

        # determine display string
        if due_date:
            if due_date == tomorrow_date:
                disp = "Tomorrow"
            elif due_date == today_date:
                disp = "Today"
            elif due_date.isocalendar()[1] == today_date.isocalendar()[1]:
                disp = calendar.day_name[due_date.weekday()]
            else:
                disp = f"{calendar.month_name[due_date.month]} {due_date.day}"
            sort_dt = due_date
        else:
            # weekday(s) only
            names = [calendar.day_name[i] for i in idxs]
            disp = "/".join(names)
            dates = [today_date + timedelta(days=(i - today_idx)) for i in idxs]
            sort_dt = max(dates)

        buckets[section].append({
            'orig_idx': idx,
            'section': section,
            'desc': desc,
            'due':  disp,
            'stat': stat,
            'sort': sort_dt
        })  
    
    # flatten in the order past -> today -> later with 7 day cutoff
    cutoff = today_date - timedelta(days=7)
    buckets['past'] = [
        t for t in buckets['past']
        if t['stat'] == 'done' and t['sort'] >= cutoff
    ]
    display = []
    for sec in ('past','today','later'):
        lst = sorted(buckets[sec], key=lambda t: t['sort'], reverse=True)
        display.extend(lst)
    return display

# ─── CLI Entrypoint ────────────────────────────────────────────────────────────

if __name__ == '__main__':
    p   = argparse.ArgumentParser(prog='todo')
    sub = p.add_subparsers(dest='cmd')
    sub.add_parser('list')
    a = sub.add_parser('add');   a.add_argument('desc'); a.add_argument('due')
    r = sub.add_parser('rm');    r.add_argument('index', type=int)
    d = sub.add_parser('done');  d.add_argument('index', type=int)
    uf = sub.add_parser('unfinished'); uf.add_argument('index', type=int)
    u = sub.add_parser('undo')
    args = p.parse_args()

    if   args.cmd == 'add':  add_task(args.desc, args.due)
    elif args.cmd == 'rm':   remove_task(args.index)
    elif args.cmd == 'done': mark_done(args.index)
    elif args.cmd == 'unfinished': unmark_done(args.index)
    elif args.cmd == 'undo': undo_last()
    else:                    list_tasks()
