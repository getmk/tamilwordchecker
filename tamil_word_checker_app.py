import re
from collections import Counter, defaultdict
import csv
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

# -----------------------------
# 🔹 Constants
# -----------------------------
SYNONYMS = {
    "அவன்": ["இவன்", "அந்தவன்"],
    "அவள்": ["இவள்", "அந்தவள்"],
    "சென்றான்": ["போனான்", "பயணித்தான்"],
    "பள்ளி": ["கல்வியகம்"],
    "நண்பன்": ["சகா", "தோழன்"]
}

STOPWORDS = {
    "அவன்", "அவள்", "அவர்கள்", "நான்", "நீ", "நாம்",
    "இது", "அது", "என்று", "என", "ஒரு", "இந்த"
}

COLORS = [
    "lightyellow", "lightgoldenrod", "khaki",
    "lightgreen", "palegreen", "springgreen",
    "lightblue", "skyblue", "deepskyblue",
    "paleturquoise", "turquoise", "aquamarine",
    "lightcyan", "cyan",
    "lavender", "thistle", "plum", "violet",
    "mistyrose", "lightpink", "pink",
    "lightsalmon", "salmon", "coral",
    "wheat", "burlywood", "tan",
    "gainsboro", "lightgray"
]

# -----------------------------
# 🔹 Utility Functions
# -----------------------------
def normalize_word(word):
    """Remove Tamil suffixes for variation detection"""
    suffixes = ["ன்", "ான்", "ின்", "ிறான்", "த்தான்", "ட்டான்"]
    for suf in suffixes:
        if word.endswith(suf):
            return word[:-len(suf)]
    return word

def extract_tamil_words(text):
    """Extract only Tamil words from text"""
    return re.findall(r'[\u0B80-\u0BFF]+', text)

def is_tamil_char(char):
    """Check if character is Tamil Unicode"""
    return '\u0B80' <= char <= '\u0BFF'

def is_whole_word(text, start_idx, word):
    """Check if word at position is a whole word (not part of larger word)"""
    before = text[start_idx - 1] if start_idx > 0 else " "
    after_idx = start_idx + len(word)
    after = text[after_idx] if after_idx < len(text) else " "
    return not is_tamil_char(before) and not is_tamil_char(after)

# -----------------------------
# 🔹 File Analysis Functions
# -----------------------------
def process_file(file_path, ignore_stopwords, detect_variations):
    """Process file and return word counts and line numbers"""
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    word_counts = Counter()
    word_lines = defaultdict(list)

    for line_no, line in enumerate(lines, start=1):
        words = extract_tamil_words(line)
        
        for word in words:
            if not word.strip():
                continue
            
            if ignore_stopwords and word in STOPWORDS:
                continue
            
            key = normalize_word(word) if detect_variations else word
            word_counts[key] += 1
            word_lines[key].append(line_no)

    return word_counts, word_lines

def analyze_file(file_path, ignore_var, variation_var, result_box):
    """Display file analysis results"""
    if not file_path:
        return None
    
    word_counts, word_lines = process_file(
        file_path, 
        ignore_var.get(), 
        variation_var.get()
    )
    
    result_box.delete(1.0, tk.END)
    result_box.insert(tk.END, "🔁 Repeated Tamil Words:\n\n")
    
    items = sorted(word_counts.items())
    for word, count in items:
        if count > 1:
            lines = sorted(set(word_lines[word]))
            result_box.insert(tk.END, f"{word} : {count} times | Lines: {lines}\n")
    
    return word_counts

# -----------------------------
# 🔹 Live Mode Functions
# -----------------------------
def get_word_color_map(text, ignore_stopwords, detect_variations):
    """Generate color map for duplicate words"""
    words = extract_tamil_words(text)
    
    if ignore_stopwords:
        words = [w for w in words if w not in STOPWORDS]
    
    if detect_variations:
        words = [normalize_word(w) for w in words]
    
    counts = Counter(words)
    
    color_map = {}
    color_index = 0
    
    for word, count in counts.items():
        if count > 1:
            color_map[word] = COLORS[color_index % len(COLORS)]
            color_index += 1
    
    return color_map, counts, len(words)

def apply_highlights(editor, color_map):
    """Apply color highlights to duplicate words"""
    # Remove existing highlight tags
    for tag in editor.tag_names():
        if tag.startswith("word_"):
            editor.tag_remove(tag, "1.0", tk.END)
    
    text_content = editor.get("1.0", tk.END)
    
    for word, color in color_map.items():
        tag_name = f"word_{word}"
        start = "1.0"
        
        while True:
            pos = editor.search(word, start, stopindex=tk.END)
            if not pos:
                break
            
            full_index = len(editor.get("1.0", pos))
            
            if is_whole_word(text_content, full_index, word):
                end = f"{pos}+{len(word)}c"
                editor.tag_add(tag_name, pos, end)
            
            start = f"{pos}+{len(word)}c"
        
        editor.tag_config(tag_name, background=color)

def update_sidebar(word_listbox, counts, color_map):
    """Update the side panel with duplicate words"""
    word_listbox.delete(0, tk.END)
    
    for word, count in counts.most_common():
        if count >= 2:
            word_listbox.insert(tk.END, f"{word} ({count})")
            word_listbox.itemconfig(tk.END, bg=color_map.get(word, "white"))

def check_word_limit(editor, total_words, limit_entry, buffer_entry):
    """Check and apply word limit alerts"""
    try:
        limit = int(limit_entry.get())
        buffer = int(buffer_entry.get())
    except:
        return
    
    if limit <= 0:
        return
    
    if total_words >= limit:
        editor.config(bg="#ffcccc")  # Light red
    elif total_words >= (limit - buffer):
        editor.config(bg="#fff2cc")  # Light yellow
    else:
        editor.config(bg="white")

def highlight_live(editor, word_listbox, limit_entry, buffer_entry, 
                   word_count_var, ignore_var, variation_var):
    """Main function for live highlighting"""
    text = editor.get("1.0", tk.END)
    
    # Get color map and counts
    color_map, counts, total_words = get_word_color_map(
        text, ignore_var.get(), variation_var.get()
    )
    
    # Update UI
    word_count_var.set(str(total_words))
    apply_highlights(editor, color_map)
    update_sidebar(word_listbox, counts, color_map)
    check_word_limit(editor, total_words, limit_entry, buffer_entry)

# -----------------------------
# 🔹 Period Insertion
# -----------------------------
def insert_period(editor, highlight_func):
    """Insert period that works with Tamil IME - removes any unwanted spaces"""
    pos = editor.index(tk.INSERT)
    
    # Keep deleting spaces until no more spaces before cursor
    while True:
        # Check character before cursor
        if int(editor.index(f"{pos} -1c").split('.')[1]) > 0:
            char_before = editor.get(f"{pos} -1c", pos)
            if char_before == " ":
                editor.delete(f"{pos} -1c", pos)
                pos = editor.index(tk.INSERT)  # Update position
            else:
                break
        else:
            break
    
    # Insert period
    editor.insert(pos, ".")
    
    # Move cursor after period
    editor.mark_set(tk.INSERT, f"{pos}+1c")
    
    # Update highlights
    highlight_func()

# -----------------------------
# 🔹 Word Navigation
# -----------------------------
def focus_word(event, editor, word_listbox):
    """Highlight word when clicked in sidebar"""
    selection = word_listbox.get(tk.ACTIVE)
    if not selection:
        return
    
    word = selection.split(" ")[0]
    
    # Remove previous focus highlight
    editor.tag_remove("focus", "1.0", tk.END)
    
    # Find and highlight all occurrences
    text_content = editor.get("1.0", tk.END)
    start = "1.0"
    
    while True:
        pos = editor.search(word, start, stopindex=tk.END)
        if not pos:
            break
        
        full_index = len(editor.get("1.0", pos))
        
        if is_whole_word(text_content, full_index, word):
            end = f"{pos}+{len(word)}c"
            editor.tag_add("focus", pos, end)
        
        start = f"{pos}+{len(word)}c"
    
    editor.tag_config("focus", background="blue", foreground="white")

# -----------------------------
# 🔹 File Operations
# -----------------------------
def save_content(editor):
    """Save editor content to file"""
    text = editor.get("1.0", tk.END).strip()
    
    if not text:
        messagebox.showwarning("Warning", "Nothing to save!")
        return False
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt")],
        initialfile="tamil_text.txt"
    )
    
    if not file_path:
        return False
    
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    
    messagebox.showinfo("Success", "File saved successfully!")
    return True

def clear_editor(editor, word_listbox, word_count_var):
    """Clear all content from editor"""
    confirm = messagebox.askyesno("Confirm", "Clear all text?")
    if confirm:
        editor.delete("1.0", tk.END)
        word_listbox.delete(0, tk.END)
        word_count_var.set("0")
        editor.config(bg="white")

def export_csv(word_counts):
    """Export word counts to CSV"""
    if not word_counts:
        messagebox.showwarning("Warning", "No data to export!")
        return
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")]
    )
    
    if not file_path:
        return
    
    with open(file_path, "w", newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(["Word", "Count"])
        for word, count in word_counts.most_common():
            writer.writerow([word, count])
    
    messagebox.showinfo("Success", "CSV saved successfully!")

# -----------------------------
# 🔹 GUI Setup
# -----------------------------
def create_file_tab(notebook, ignore_var, variation_var):
    """Create File Analysis tab"""
    file_tab = tk.Frame(notebook)
    notebook.add(file_tab, text="📂 File Analysis")
    
    # Variables
    current_counts = None
    
    # Widgets
    btn_frame = tk.Frame(file_tab)
    btn_frame.pack(pady=10)
    
    result_box = tk.Text(file_tab, wrap=tk.WORD, font=("LATHA", 11))
    result_box.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
    
    def analyze_and_display():
        nonlocal current_counts
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            current_counts = analyze_file(file_path, ignore_var, variation_var, result_box)
    
    def export_current():
        export_csv(current_counts)
    
    tk.Button(btn_frame, text="Select & Analyze File", command=analyze_and_display).pack(side="left", padx=5)
    tk.Button(btn_frame, text="Export CSV", command=export_current).pack(side="left", padx=5)
    
    return file_tab

def create_live_tab(notebook, app, ignore_var, variation_var, limit_entry, buffer_entry, word_count_var):
    """Create Live Typing tab"""
    live_tab = tk.Frame(notebook)
    notebook.add(live_tab, text="✍️ Live Typing")
    
    # Create main container
    main_container = tk.Frame(live_tab)
    main_container.pack(expand=True, fill="both")
    
    # Left side - Editor
    editor_frame = tk.Frame(main_container)
    editor_frame.pack(side="left", expand=True, fill="both")
    
    tk.Label(editor_frame, text="Type or Paste Tamil Text Below:", 
             font=("LATHA", 10)).pack(pady=5)
    
    # Editor with scrollbar
    editor_container = tk.Frame(editor_frame)
    editor_container.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
    
    editor_scrollbar = tk.Scrollbar(editor_container)
    editor_scrollbar.pack(side="right", fill="y")
    
    editor = tk.Text(
        editor_container,
        wrap=tk.WORD,
        yscrollcommand=editor_scrollbar.set,
        undo=True,
        font=("LATHA", 12)
    )
    editor.pack(side="left", expand=True, fill=tk.BOTH)
    editor_scrollbar.config(command=editor.yview)
    
    # Right side - Sidebar
    sidebar = tk.Frame(main_container, width=250)
    sidebar.pack(side="right", fill="y", padx=5, pady=5)
    
    tk.Label(sidebar, text="📊 Duplicate Words", font=("LATHA", 11, "bold")).pack(pady=5)
    
    listbox_scrollbar = tk.Scrollbar(sidebar)
    listbox_scrollbar.pack(side="right", fill="y")
    
    word_listbox = tk.Listbox(
        sidebar, 
        yscrollcommand=listbox_scrollbar.set,
        font=("LATHA", 10)
    )
    word_listbox.pack(expand=True, fill="both")
    listbox_scrollbar.config(command=word_listbox.yview)
    
    # Button frame
    button_frame = tk.Frame(editor_frame)
    button_frame.pack(fill="x", pady=5)
    
    # Create wrapper function for highlight
    def update_highlight():
        highlight_live(
            editor, word_listbox, limit_entry, buffer_entry,
            word_count_var, ignore_var, variation_var
        )
    
    # Buttons
    tk.Button(button_frame, text="💾 Save", 
              command=lambda: save_content(editor)).pack(side="left", padx=5)
    tk.Button(button_frame, text="🧹 Clear", 
              command=lambda: clear_editor(editor, word_listbox, word_count_var)).pack(side="left", padx=5)
    tk.Button(button_frame, text="புள்ளி (.)", 
              command=lambda: insert_period(editor, update_highlight),
              bg="#e0e0e0", font=("LATHA", 10)).pack(side="left", padx=5)
    
    # Bind events
    def schedule_highlight(event=None):
        app.after_idle(update_highlight)
    
    editor.bind("<KeyRelease>", schedule_highlight)
    editor.bind("<Control-s>", lambda e: save_content(editor))
    editor.bind("<Control-l>", lambda e: clear_editor(editor, word_listbox, word_count_var))
    editor.bind("<Control-period>", lambda e: insert_period(editor, update_highlight))
    editor.bind("<Control-z>", lambda e: editor.edit_undo())
    editor.bind("<Control-y>", lambda e: editor.edit_redo())
    
    word_listbox.bind("<<ListboxSelect>>", 
                      lambda e: focus_word(e, editor, word_listbox))
    
    return live_tab
def create_options_frame(parent):
    """Create options and controls frame"""
    options_frame = tk.Frame(parent)
    options_frame.pack(fill="x", pady=5, padx=10)
    
    # Sort options
    sort_var = tk.StringVar(value="count")
    tk.Label(options_frame, text="Sort:").pack(side="left")
    tk.Radiobutton(options_frame, text="Count", variable=sort_var, value="count").pack(side="left")
    tk.Radiobutton(options_frame, text="A-Z", variable=sort_var, value="alpha").pack(side="left")
    
    # Word count display
    tk.Label(options_frame, text="Total Words:").pack(side="left", padx=(20, 5))
    word_count_var = tk.StringVar(value="0")
    word_count_display = tk.Label(options_frame, textvariable=word_count_var)
    word_count_display.pack(side="left")
    
    # Ignore stopwords
    ignore_var = tk.BooleanVar()
    tk.Checkbutton(options_frame, text="Ignore Common Words", 
                   variable=ignore_var).pack(side="left", padx=10)
    
    # Detect variations
    variation_var = tk.BooleanVar()
    tk.Checkbutton(options_frame, text="Detect Variations", 
                   variable=variation_var).pack(side="left")
    
    # Alert limit
    tk.Label(options_frame, text="Alert Limit:").pack(side="left", padx=(20, 5))
    limit_entry = tk.Entry(options_frame, width=8)
    limit_entry.pack(side="left")
    limit_entry.insert(0, "111")
    
    # Warning buffer
    tk.Label(options_frame, text="Buffer:").pack(side="left", padx=(10, 5))
    buffer_entry = tk.Entry(options_frame, width=5)
    buffer_entry.pack(side="left")
    buffer_entry.insert(0, "10")
    
    return ignore_var, variation_var, limit_entry, buffer_entry, word_count_var

def create_menu(app, editor, word_listbox, word_count_var):
    """Create application menu"""
    menu_bar = tk.Menu(app)
    app.config(menu=menu_bar)
    
    edit_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Edit", menu=edit_menu)
    
    edit_menu.add_command(label="Undo (Ctrl+Z)", command=editor.edit_undo)
    edit_menu.add_command(label="Redo (Ctrl+Y)", command=editor.edit_redo)
    edit_menu.add_separator()
    edit_menu.add_command(label="Save (Ctrl+S)", 
                          command=lambda: save_content(editor))
    edit_menu.add_command(label="Clear (Ctrl+L)", 
                          command=lambda: clear_editor(editor, word_listbox, word_count_var))
    edit_menu.add_separator()
    edit_menu.add_command(label="Insert Period (Ctrl+.)", 
                          command=lambda: insert_period(editor, lambda: None))

# -----------------------------
# 🔹 Main Application
# -----------------------------
def main():
    app = tk.Tk()
    app.title("Tamil Word Checker Pro")
    app.state('zoomed')
    
    # Set font
    app.option_add("*Font", ("LATHA", 11))
    
    # Create notebook for tabs
    notebook = ttk.Notebook(app)
    notebook.pack(expand=True, fill="both", padx=5, pady=5)
    
    # Create options frame first to get variables
    ignore_var, variation_var, limit_entry, buffer_entry, word_count_var = create_options_frame(app)
    
    # Create tabs (pass the variables)
    create_file_tab(notebook, ignore_var, variation_var)
    live_tab = create_live_tab(notebook, app, ignore_var, variation_var, limit_entry, buffer_entry, word_count_var)
    
    # Create menu (we'll create it after editor is created)
    # For now, we'll create a placeholder
    menu_bar = tk.Menu(app)
    app.config(menu=menu_bar)
    
    app.mainloop()

if __name__ == "__main__":
    main()