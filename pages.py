from utils import Alogger

from tkinter import *
from tkinter import ttk
from PIL import ImageTk, Image, ImageDraw

import db

alogger = Alogger("pages")

FONT         = ('Segoe UI', 11)
FONT_BOLD    = ('Segoe UI', 11, 'bold')
FONT_HEADING = ('Segoe UI', 16, 'bold')

PANEL_BG  = '#1e1e2e'
BTN_DARK  = '#2d2d44'
BTN_DEL   = '#922b21'
BTN_LIGHT = '#e8e8e8'


def _apply_styles():
    style = ttk.Style()
    style.theme_use('clam')
    style.configure("Treeview",           font=FONT,      rowheight=26,
                    background='#f5f5f5', fieldbackground='#f5f5f5', foreground='#1e1e2e')
    style.configure("Treeview.Heading",   font=FONT_BOLD,
                    background=PANEL_BG,  foreground='white', relief='flat')
    style.map("Treeview.Heading",         background=[('active', BTN_DARK)])
    style.configure("TCombobox",          font=FONT)

_bg_original = None

def _set_background(root, overlays=None):
    """
    overlays: list of (relx, rely, relwidth, relheight) rectangles to draw
              as semi-transparent dark panels baked into the background image.
    """
    global _bg_original
    if _bg_original is None:
        try:
            _bg_original = Image.open("./library.jpg")
        except Exception:
            return

    root._bg_overlays = overlays or []

    if not hasattr(root, '_bg_label') or not root._bg_label.winfo_exists():
        root._bg_label = Label(root)
        root._bg_label.place(relx=0, rely=0, relwidth=1, relheight=1)

    root._bg_label.lower()
    debounce = [None]

    def _redraw():
        w = root.winfo_width()
        h = root.winfo_height()
        if w < 2 or h < 2:
            return
        base = _bg_original.resize((w, h), Image.LANCZOS).convert('RGBA')
        for (rx, ry, rw, rh) in root._bg_overlays:
            x0, y0 = int(rx * w), int(ry * h)
            x1, y1 = int((rx + rw) * w), int((ry + rh) * h)
            panel = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            ImageDraw.Draw(panel).rectangle([x0, y0, x1, y1], fill=(30, 30, 46, 195))
            base = Image.alpha_composite(base, panel)
        img = ImageTk.PhotoImage(base.convert('RGB'))
        root._bg_label.config(image=img)
        root._bg_label.image = img
        root._bg_label.lower()

    def _on_resize(event):
        if event.widget is not root:
            return
        if debounce[0]:
            root.after_cancel(debounce[0])
        debounce[0] = root.after(50, _redraw)

    root.bind('<Configure>', _on_resize)
    root.after(10, _redraw)

def _heading(root, text):
    Label(root, text=text, bg=PANEL_BG, fg='white', font=FONT_HEADING,
          pady=8).place(relx=0.2, rely=0.04, relwidth=0.6, relheight=0.09)

def _back_button(root, session):
    Button(root, text="Back", bg=BTN_LIGHT, fg='#1e1e2e', font=FONT,
           relief='flat', cursor='hand2',
           command=lambda: main_page(root, session)).place(relx=0.55, rely=0.9, relwidth=0.15, relheight=0.07)


# ─── Main Page ────────────────────────────────────────────────────────────────

def main_page(root, session):
    alogger.debug("Main page active")
    for child in root.winfo_children():
        child.destroy()

    _apply_styles()
    _set_background(root, overlays=[(0.03, 0.28, 0.94, 0.38)])

    btn_cfg = dict(bg=BTN_DARK, fg='white', font=FONT_BOLD, relief='flat', cursor='hand2')

    Button(root, text="Add Book",       **btn_cfg, command=lambda: page_add_book(root, session)).place(   relx=0.03, rely=0.15, relwidth=0.29, relheight=0.1)
    Button(root, text="Delete Book",    **btn_cfg, command=lambda: page_remove_book(root, session)).place( relx=0.35, rely=0.15, relwidth=0.29, relheight=0.1)
    Button(root, text="View Book List", **btn_cfg, command=lambda: page_list_book(root, session)).place(   relx=0.67, rely=0.15, relwidth=0.29, relheight=0.1)

    Button(root, text="Manage Subjects",     **btn_cfg, command=lambda: page_manage_subjects(root, session)).place(      relx=0.05, rely=0.38, relwidth=0.42, relheight=0.1)
    Button(root, text="Manage Sub-Subjects", **btn_cfg, command=lambda: page_manage_subcategories(root, session)).place( relx=0.52, rely=0.38, relwidth=0.42, relheight=0.1)
    Button(root, text="Manage Publishers",   **btn_cfg, command=lambda: page_manage_publishers(root, session)).place(    relx=0.05, rely=0.52, relwidth=0.42, relheight=0.1)
    Button(root, text="Manage Authors",      **btn_cfg, command=lambda: page_manage_authors(root, session)).place(       relx=0.52, rely=0.52, relwidth=0.42, relheight=0.1)


# ─── Shared helpers ───────────────────────────────────────────────────────────

def _searchable_combo(parent, get_values_fn, add_new_label, on_add_new, on_select=None):
    combo = ttk.Combobox(parent)

    def refresh_values():
        combo['values'] = [add_new_label] + get_values_fn()

    def filter_values(event):
        typed = combo.get()
        if not typed or typed == add_new_label:
            refresh_values()
            return
        filtered = [v for v in get_values_fn() if typed.lower() in v.lower()]
        combo['values'] = [add_new_label] + filtered

    def on_selected(event):
        if combo.get() == add_new_label:
            combo.set('')
            on_add_new(refresh_values, combo)
        elif on_select:
            on_select(combo.get())

    combo.bind('<KeyRelease>', filter_values)
    combo.bind('<<ComboboxSelected>>', on_selected)
    refresh_values()
    return combo


def _make_popup(root, title, fields, on_submit):
    ROW_H, GAP, TOP, BTN_H = 28, 10, 15, 30
    h = TOP + len(fields) * (ROW_H + GAP) + BTN_H + 20
    win = Toplevel(root)
    win.title(title)
    win.geometry(f"400x{h}")
    win.resizable(False, False)
    win.grab_set()

    entries = []
    for i, (lbl, _) in enumerate(fields):
        y = TOP + i * (ROW_H + GAP)
        Label(win, text=lbl, font=FONT).place(x=10, y=y, width=130, height=ROW_H)
        e = Entry(win, font=FONT)
        e.place(x=145, y=y, width=240, height=ROW_H)
        entries.append(e)

    entries[0].focus()

    def submit():
        values = [e.get().strip() for e in entries]
        for val, (_, required) in zip(values, fields):
            if required and not val:
                return
        on_submit(values)
        win.destroy()

    btn_y = TOP + len(fields) * (ROW_H + GAP) + 5
    Button(win, text="Add",    font=FONT, command=submit,      bg=BTN_DARK,  fg='white', relief='flat').place(x=85,  y=btn_y, width=90, height=BTN_H)
    Button(win, text="Cancel", font=FONT, command=win.destroy, bg=BTN_LIGHT, fg='#1e1e2e', relief='flat').place(x=195, y=btn_y, width=90, height=BTN_H)
    win.bind('<Return>', lambda e: submit())


# ─── Add Book ─────────────────────────────────────────────────────────────────

def page_add_book(root, session):
    for child in root.winfo_children():
        child.destroy()

    _set_background(root, overlays=[(0.03, 0.13, 0.94, 0.46)])
    _heading(root, "Add Book")

    lbl  = dict(bg=PANEL_BG, fg='white', font=FONT)
    rh   = 0.048
    step = 0.062

    def row(i): return 0.17 + i * step

    # ── Full-width: Title and Author ──
    fw_lx, fw_ex, fw_ew = 0.05, 0.22, 0.73   # label x, entry x, entry width

    Label(root, text="Title:",  **lbl).place(relx=fw_lx, rely=row(0), relheight=rh)
    title_entry = Entry(root, font=FONT)
    title_entry.place(relx=fw_ex, rely=row(0), relwidth=fw_ew, relheight=rh)

    author_map = [{}]
    Label(root, text="Author:", **lbl).place(relx=fw_lx, rely=row(1), relheight=rh)

    def open_add_author(refresh_fn, combo):
        def done(vals):
            db.add_author(session, vals[0], vals[1], vals[2], vals[3])
            author_map[0] = db.build_author_map(session)
            refresh_fn()
            combo.set(f"{vals[0]} {vals[1]}")
        _make_popup(root, "Add Author", [
            ("First Name", True), ("Last Name", True),
            ("Affiliation", False), ("Wiki Link", False)
        ], done)

    author_combo = _searchable_combo(
        root,
        lambda: list(db.build_author_map(session).keys()),
        "Add New Author...", open_add_author
    )
    author_combo.place(relx=fw_ex, rely=row(1), relwidth=fw_ew, relheight=rh)

    # ── Two columns below ──
    ll_x, lf_x, lw = 0.05, 0.22, 0.26   # left label x, left field x, left field width
    rl_x, rf_x, rw = 0.54, 0.70, 0.27   # right label x, right field x, right field width

    # Left: Publisher, Subject, Sub-Subject, Dewey
    Label(root, text="Publisher:",   **lbl).place(relx=ll_x, rely=row(2), relheight=rh)
    def open_add_publisher(refresh_fn, combo):
        def done(vals):
            db.add_publisher(session, vals[0], vals[1], vals[2])
            refresh_fn()
            combo.set(vals[0])
        _make_popup(root, "Add Publisher", [
            ("Name", True), ("Country", False), ("Website", False)
        ], done)
    publisher_combo = _searchable_combo(
        root,
        lambda: [p.name for p in db.get_all_publishers(session)],
        "Add New Publisher...", open_add_publisher
    )
    publisher_combo.place(relx=lf_x, rely=row(2), relwidth=lw, relheight=rh)

    subsubject_combo = [None]
    Label(root, text="Subject:",     **lbl).place(relx=ll_x, rely=row(3), relheight=rh)
    def on_subject_selected(subject_name):
        subs = [s.name for s in db.get_subcategories_by_subject(session, subject_name)]
        subsubject_combo[0]['values'] = ["Add New Sub-Subject..."] + subs
        subsubject_combo[0].set('')
    def open_add_subject(refresh_fn, combo):
        def done(vals):
            db.add_subject(session, vals[0])
            refresh_fn()
            combo.set(vals[0])
            on_subject_selected(vals[0])
        _make_popup(root, "Add Subject", [("Subject Name", True)], done)
    subject_combo = _searchable_combo(
        root,
        lambda: [s.name for s in db.get_all_subjects(session)],
        "Add New Subject...", open_add_subject, on_select=on_subject_selected
    )
    subject_combo.place(relx=lf_x, rely=row(3), relwidth=lw, relheight=rh)

    Label(root, text="Sub-Subject:", **lbl).place(relx=ll_x, rely=row(4), relheight=rh)
    def open_add_subsubject(refresh_fn, combo):
        ROW_H, GAP, TOP, BTN_H = 28, 10, 15, 30
        win = Toplevel(root)
        win.title("Add Sub-Subject")
        win.geometry("400x150")
        win.resizable(False, False)
        win.grab_set()
        Label(win, text="Subject:", font=FONT).place(x=10, y=TOP, width=130, height=ROW_H)
        subj_cb = ttk.Combobox(win, values=[s.name for s in db.get_all_subjects(session)],
                               state='readonly', font=FONT)
        subj_cb.place(x=145, y=TOP, width=240, height=ROW_H)
        cur = subject_combo.get().strip()
        if cur and cur != "Add New Subject...":
            subj_cb.set(cur)
        y2 = TOP + ROW_H + GAP
        Label(win, text="Sub-Subject:", font=FONT).place(x=10, y=y2, width=130, height=ROW_H)
        name_e = Entry(win, font=FONT)
        name_e.place(x=145, y=y2, width=240, height=ROW_H)
        name_e.focus()
        def submit():
            subj_name = subj_cb.get().strip()
            name = name_e.get().strip()
            if not subj_name or not name:
                return
            subj_obj = db.get_subject_by_name(session, subj_name)
            if not subj_obj:
                return
            db.add_subcategory(session, subj_obj, name)
            if subject_combo.get().strip() != subj_name:
                subject_combo.set(subj_name)
            on_subject_selected(subj_name)
            combo.set(name)
            win.destroy()
        btn_y = y2 + ROW_H + GAP + 5
        Button(win, text="Add",    font=FONT, command=submit,      bg=BTN_DARK,  fg='white',    relief='flat').place(x=85,  y=btn_y, width=90, height=BTN_H)
        Button(win, text="Cancel", font=FONT, command=win.destroy, bg=BTN_LIGHT, fg='#1e1e2e', relief='flat').place(x=195, y=btn_y, width=90, height=BTN_H)
        win.bind('<Return>', lambda e: submit())
    subsubject_combo[0] = _searchable_combo(
        root, lambda: [], "Add New Sub-Subject...", open_add_subsubject
    )
    subsubject_combo[0].place(relx=lf_x, rely=row(4), relwidth=lw, relheight=rh)

    Label(root, text="Dewey Code:",  **lbl).place(relx=ll_x, rely=row(5), relheight=rh)
    dewey_entry = Entry(root, font=FONT)
    dewey_entry.place(relx=lf_x, rely=row(5), relwidth=lw, relheight=rh)

    # Right: ISBN, Edition, Year, Type
    Label(root, text="ISBN:",        **lbl).place(relx=rl_x, rely=row(2), relheight=rh)
    isbn_entry = Entry(root, font=FONT)
    isbn_entry.place(relx=rf_x, rely=row(2), relwidth=rw, relheight=rh)

    Label(root, text="Edition:",     **lbl).place(relx=rl_x, rely=row(3), relheight=rh)
    edition_entry = Entry(root, font=FONT)
    edition_entry.place(relx=rf_x, rely=row(3), relwidth=rw, relheight=rh)

    Label(root, text="Pub. Year:",   **lbl).place(relx=rl_x, rely=row(4), relheight=rh)
    year_entry = Entry(root, font=FONT)
    year_entry.place(relx=rf_x, rely=row(4), relwidth=rw, relheight=rh)

    Label(root, text="Type:",        **lbl).place(relx=rl_x, rely=row(5), relheight=rh)
    type_combo = ttk.Combobox(root, values=["Physical", "Electronic"], state='readonly', font=FONT)
    type_combo.place(relx=rf_x, rely=row(5), relwidth=rw, relheight=rh)

    def submit():
        title = title_entry.get().strip()
        if not title:
            return
        author_map[0] = db.build_author_map(session)
        author = author_map[0].get(author_combo.get().strip())
        db.add_book(
            session, title,
            isbn_entry.get().strip(),
            author,
            publisher_combo.get().strip(),
            subject_combo.get().strip(),
            subsubject_combo[0].get().strip(),
            edition_entry.get().strip(),
            year_entry.get().strip(),
            type_combo.get().strip(),
            dewey_entry.get().strip(),
        )
        alogger.debug("Book added")
        page_add_book(root, session)

    Button(root, text="Submit", bg=BTN_DARK, fg='white', font=FONT,
           relief='flat', cursor='hand2', command=submit).place(relx=0.28, rely=0.9, relwidth=0.18, relheight=0.07)
    _back_button(root, session)


# ─── List / Delete Books ──────────────────────────────────────────────────────

def _book_tree(frame, books):
    cols = ("Title", "Authors", "Publisher", "Subject", "Type", "Year", "Dewey")
    tree = ttk.Treeview(frame, columns=cols, show='headings')
    tree.column("Title",     anchor=W, width=160)
    tree.column("Authors",   anchor=W, width=130)
    tree.column("Publisher", anchor=W, width=100)
    tree.column("Subject",   anchor=W, width=90)
    tree.column("Type",      anchor=CENTER, width=80)
    tree.column("Year",      anchor=CENTER, width=55)
    tree.column("Dewey",     anchor=W, width=70)
    for col in cols:
        tree.heading(col, text=col)
    tree.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)
    return tree


def _fill_book_row(tree, row, use_iid=False):
    authors = ", ".join(db.author_display_name(a) for a in row.authors)
    publisher = row.publisher.name if row.publisher else ""
    subject   = row.primary_subject.name if row.primary_subject else ""
    vals = (row.title, authors, publisher, subject,
            row.book_type or "", row.publication_year or "", row.dewey_code or "")
    if use_iid:
        tree.insert('', 'end', iid=str(row.universal_id), values=vals)
    else:
        tree.insert('', 'end', values=vals)


def page_list_book(root, session):
    for child in root.winfo_children():
        child.destroy()
    _apply_styles()
    _set_background(root, overlays=[(0.03, 0.13, 0.94, 0.76)])
    _heading(root, "Book List")

    lbl = dict(bg=PANEL_BG, fg='white', font=FONT)

    # ── Filter bar ──
    filter_frame = Frame(root, bg=PANEL_BG)
    filter_frame.place(relx=0.03, rely=0.16, relwidth=0.94, relheight=0.07)

    Label(filter_frame, text="Subject:", **lbl).place(relx=0.0, rely=0.1, relheight=0.8, relwidth=0.1)
    subj_filter = ttk.Combobox(filter_frame, state='readonly', font=FONT)
    subj_filter.place(relx=0.11, rely=0.1, relwidth=0.25, relheight=0.8)

    Label(filter_frame, text="Sub-Subject:", **lbl).place(relx=0.38, rely=0.1, relheight=0.8, relwidth=0.14)
    sub_filter = ttk.Combobox(filter_frame, state='readonly', font=FONT)
    sub_filter.place(relx=0.53, rely=0.1, relwidth=0.25, relheight=0.8)

    # ── Book tree ──
    frame = Frame(root, bg=PANEL_BG)
    frame.place(relx=0.03, rely=0.24, relwidth=0.94, relheight=0.62)
    tree = _book_tree(frame, [])

    def refresh():
        for item in tree.get_children():
            tree.delete(item)
        subj_name = subj_filter.get()
        sub_name  = sub_filter.get()
        for bk in db.get_all_books(session):
            if subj_name and (not bk.primary_subject or bk.primary_subject.name != subj_name):
                continue
            if sub_name and (not bk.subcategory_subject or bk.subcategory_subject.name != sub_name):
                continue
            _fill_book_row(tree, bk)

    def on_subject_filter(event=None):
        subs = [s.name for s in db.get_subcategories_by_subject(session, subj_filter.get())]
        sub_filter['values'] = [''] + subs
        sub_filter.set('')
        refresh()

    def on_sub_filter(event=None):
        refresh()

    subj_names = [''] + [s.name for s in db.get_all_subjects(session)]
    subj_filter['values'] = subj_names
    subj_filter.bind('<<ComboboxSelected>>', on_subject_filter)
    sub_filter.bind('<<ComboboxSelected>>', on_sub_filter)

    Button(filter_frame, text="Show All", bg=BTN_DARK, fg='white', font=FONT,
           relief='flat', cursor='hand2',
           command=lambda: [subj_filter.set(''), sub_filter.set(''), refresh()]).place(
               relx=0.8, rely=0.1, relwidth=0.18, relheight=0.8)

    refresh()
    _back_button(root, session)


def page_remove_book(root, session):
    for child in root.winfo_children():
        child.destroy()
    _apply_styles()
    _set_background(root, overlays=[(0.03, 0.13, 0.94, 0.76)])
    _heading(root, "Delete Book")

    frame = Frame(root, bg=PANEL_BG)
    frame.place(relx=0.03, rely=0.17, relwidth=0.94, relheight=0.68)

    tree = _book_tree(frame, [])

    def refresh():
        for item in tree.get_children():
            tree.delete(item)
        for row in db.get_all_books(session):
            _fill_book_row(tree, row, use_iid=True)

    refresh()

    def delete_selected():
        for item in tree.selection():
            db.delete_book(session, int(item))
        refresh()

    Button(root, text="Delete Selected", bg=BTN_DEL, fg='white', font=FONT,
           relief='flat', cursor='hand2', command=delete_selected).place(relx=0.3, rely=0.9, relwidth=0.2, relheight=0.07)
    _back_button(root, session)


# ─── Manage Subjects ──────────────────────────────────────────────────────────

def _simple_manage_page(root, session, title, get_fn, add_fn, delete_fn, col_label):
    for child in root.winfo_children():
        child.destroy()
    _apply_styles()
    _set_background(root, overlays=[(0.1, 0.17, 0.8, 0.68)])
    _heading(root, title)

    treeFrame = Frame(root, bg=PANEL_BG)
    treeFrame.place(relx=0.1, rely=0.2, relwidth=0.8, relheight=0.5)

    tree = ttk.Treeview(treeFrame, columns=(col_label,), show='headings', height=10)
    tree.column(col_label, anchor=W)
    tree.heading(col_label, text=col_label)
    tree.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)

    def refresh():
        for item in tree.get_children():
            tree.delete(item)
        for row in get_fn(session):
            tree.insert('', 'end', iid=str(row.id), values=(row.name,))

    refresh()

    addFrame = Frame(root, bg=PANEL_BG)
    addFrame.place(relx=0.1, rely=0.75, relwidth=0.8, relheight=0.08)

    Label(addFrame, text=f"New {col_label}:", bg=PANEL_BG, fg='white', font=FONT).place(relx=0.0, rely=0.2, relheight=0.6)
    entry = Entry(addFrame, font=FONT)
    entry.place(relx=0.25, rely=0.1, relwidth=0.5, relheight=0.8)

    def add():
        name = entry.get().strip()
        if not name:
            return
        add_fn(session, name)
        entry.delete(0, END)
        refresh()

    def delete_selected():
        for item in tree.selection():
            delete_fn(session, int(item))
        refresh()

    Button(addFrame, text="Add", bg=BTN_DARK, fg='white', font=FONT,
           relief='flat', cursor='hand2', command=add).place(relx=0.78, rely=0.1, relwidth=0.2, relheight=0.8)
    Button(root, text="Delete Selected", bg=BTN_DEL, fg='white', font=FONT,
           relief='flat', cursor='hand2', command=delete_selected).place(relx=0.3, rely=0.9, relwidth=0.2, relheight=0.07)
    _back_button(root, session)


def page_manage_subjects(root, session):
    _simple_manage_page(root, session, "Manage Subjects",
                        db.get_all_subjects, db.add_subject, db.delete_subject, "Subject")


# ─── Manage Sub-Subjects ──────────────────────────────────────────────────────

def page_manage_subcategories(root, session):
    for child in root.winfo_children():
        child.destroy()
    _apply_styles()
    _set_background(root, overlays=[(0.05, 0.17, 0.9, 0.67)])
    _heading(root, "Manage Sub-Subjects")

    treeFrame = Frame(root, bg=PANEL_BG)
    treeFrame.place(relx=0.05, rely=0.2, relwidth=0.9, relheight=0.45)

    tree = ttk.Treeview(treeFrame, columns=("Subject", "Sub-Subject"), show='headings', height=10)
    tree.column("Subject",      anchor=W, width=200)
    tree.heading("Subject",     text="Subject")
    tree.column("Sub-Subject",  anchor=W, width=200)
    tree.heading("Sub-Subject", text="Sub-Subject")
    tree.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)

    def refresh():
        for item in tree.get_children():
            tree.delete(item)
        for row in db.get_all_subcategories(session):
            tree.insert('', 'end', iid=str(row.id),
                        values=(row.subject.name if row.subject else "", row.name))
    refresh()

    addFrame = Frame(root, bg=PANEL_BG)
    addFrame.place(relx=0.05, rely=0.7, relwidth=0.9, relheight=0.12)

    subject_list = [s.name for s in db.get_all_subjects(session)]
    Label(addFrame, text="Subject:",     bg=PANEL_BG, fg='white', font=FONT).place(relx=0.0, rely=0.1,  relheight=0.4)
    subject_combo = ttk.Combobox(addFrame, values=subject_list, state='readonly', font=FONT)
    subject_combo.place(relx=0.15, rely=0.1, relwidth=0.3, relheight=0.4)

    Label(addFrame, text="Sub-Subject:", bg=PANEL_BG, fg='white', font=FONT).place(relx=0.0, rely=0.55, relheight=0.4)
    name_entry = Entry(addFrame, font=FONT)
    name_entry.place(relx=0.15, rely=0.55, relwidth=0.3, relheight=0.4)

    def add():
        subject_name = subject_combo.get().strip()
        name = name_entry.get().strip()
        if not subject_name or not name:
            return
        db.add_subcategory(session, db.get_subject_by_name(session, subject_name), name)
        subject_combo.set('')
        name_entry.delete(0, END)
        refresh()

    def delete_selected():
        for item in tree.selection():
            db.delete_subcategory(session, int(item))
        refresh()

    Button(addFrame, text="Add", bg=BTN_DARK, fg='white', font=FONT,
           relief='flat', cursor='hand2', command=add).place(relx=0.48, rely=0.2, relwidth=0.15, relheight=0.6)
    Button(root, text="Delete Selected", bg=BTN_DEL, fg='white', font=FONT,
           relief='flat', cursor='hand2', command=delete_selected).place(relx=0.3, rely=0.9, relwidth=0.2, relheight=0.07)
    _back_button(root, session)


# ─── Manage Publishers ────────────────────────────────────────────────────────

def page_manage_publishers(root, session):
    for child in root.winfo_children():
        child.destroy()
    _apply_styles()
    _set_background(root, overlays=[(0.03, 0.14, 0.94, 0.72)])
    _heading(root, "Manage Publishers")

    treeFrame = Frame(root, bg=PANEL_BG)
    treeFrame.place(relx=0.03, rely=0.17, relwidth=0.94, relheight=0.5)

    cols = ("Name", "Country", "Website")
    tree = ttk.Treeview(treeFrame, columns=cols, show='headings', height=10)
    tree.column("Name",    anchor=W, width=180)
    tree.column("Country", anchor=W, width=120)
    tree.column("Website", anchor=W, width=250)
    for col in cols:
        tree.heading(col, text=col)
    tree.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)

    def refresh():
        for item in tree.get_children():
            tree.delete(item)
        for p in db.get_all_publishers(session):
            tree.insert('', 'end', iid=str(p.id),
                        values=(p.name, p.country or "", p.website or ""))
    refresh()

    addFrame = Frame(root, bg=PANEL_BG)
    addFrame.place(relx=0.03, rely=0.71, relwidth=0.94, relheight=0.12)

    lbl = dict(bg=PANEL_BG, fg='white', font=FONT)
    Label(addFrame, text="Name:",    **lbl).place(relx=0.0,  rely=0.1, relheight=0.38)
    name_e = Entry(addFrame, font=FONT)
    name_e.place(relx=0.1, rely=0.1, relwidth=0.22, relheight=0.38)

    Label(addFrame, text="Country:", **lbl).place(relx=0.34, rely=0.1, relheight=0.38)
    country_e = Entry(addFrame, font=FONT)
    country_e.place(relx=0.46, rely=0.1, relwidth=0.18, relheight=0.38)

    Label(addFrame, text="Website:", **lbl).place(relx=0.0,  rely=0.58, relheight=0.38)
    website_e = Entry(addFrame, font=FONT)
    website_e.place(relx=0.1, rely=0.58, relwidth=0.54, relheight=0.38)

    def add():
        name = name_e.get().strip()
        if not name:
            return
        db.add_publisher(session, name, country_e.get().strip(), website_e.get().strip())
        for e in (name_e, country_e, website_e):
            e.delete(0, END)
        refresh()

    def delete_selected():
        for item in tree.selection():
            db.delete_publisher(session, int(item))
        refresh()

    Button(addFrame, text="Add", bg=BTN_DARK, fg='white', font=FONT,
           relief='flat', cursor='hand2', command=add).place(relx=0.68, rely=0.28, relwidth=0.14, relheight=0.45)
    Button(root, text="Delete Selected", bg=BTN_DEL, fg='white', font=FONT,
           relief='flat', cursor='hand2', command=delete_selected).place(relx=0.3, rely=0.9, relwidth=0.2, relheight=0.07)
    _back_button(root, session)


# ─── Manage Authors ───────────────────────────────────────────────────────────

def page_manage_authors(root, session):
    for child in root.winfo_children():
        child.destroy()
    _apply_styles()
    _set_background(root, overlays=[(0.03, 0.14, 0.94, 0.72)])
    _heading(root, "Manage Authors")

    treeFrame = Frame(root, bg=PANEL_BG)
    treeFrame.place(relx=0.03, rely=0.17, relwidth=0.94, relheight=0.48)

    cols = ("First Name", "Last Name", "Affiliation", "Wiki")
    tree = ttk.Treeview(treeFrame, columns=cols, show='headings', height=10)
    tree.column("First Name",   anchor=W, width=120)
    tree.column("Last Name",    anchor=W, width=120)
    tree.column("Affiliation",  anchor=W, width=180)
    tree.column("Wiki",         anchor=W, width=200)
    for col in cols:
        tree.heading(col, text=col)
    tree.place(relx=0.01, rely=0.01, relwidth=0.98, relheight=0.98)

    def refresh():
        for item in tree.get_children():
            tree.delete(item)
        for a in db.get_all_authors(session):
            tree.insert('', 'end', iid=str(a.id),
                        values=(a.first_name, a.last_name,
                                a.affiliation or "", a.wiki_link or ""))
    refresh()

    addFrame = Frame(root, bg=PANEL_BG)
    addFrame.place(relx=0.03, rely=0.69, relwidth=0.94, relheight=0.14)

    lbl = dict(bg=PANEL_BG, fg='white', font=FONT)
    Label(addFrame, text="First Name:",  **lbl).place(relx=0.0,  rely=0.05, relheight=0.38)
    first_e = Entry(addFrame, font=FONT)
    first_e.place(relx=0.13, rely=0.05, relwidth=0.18, relheight=0.38)

    Label(addFrame, text="Last Name:",   **lbl).place(relx=0.33, rely=0.05, relheight=0.38)
    last_e = Entry(addFrame, font=FONT)
    last_e.place(relx=0.46, rely=0.05, relwidth=0.18, relheight=0.38)

    Label(addFrame, text="Affiliation:", **lbl).place(relx=0.0,  rely=0.57, relheight=0.38)
    affil_e = Entry(addFrame, font=FONT)
    affil_e.place(relx=0.13, rely=0.57, relwidth=0.31, relheight=0.38)

    Label(addFrame, text="Wiki Link:",   **lbl).place(relx=0.47, rely=0.57, relheight=0.38)
    wiki_e = Entry(addFrame, font=FONT)
    wiki_e.place(relx=0.60, rely=0.57, relwidth=0.25, relheight=0.38)

    def add():
        first = first_e.get().strip()
        last  = last_e.get().strip()
        if not first or not last:
            return
        db.add_author(session, first, last, affil_e.get().strip(), wiki_e.get().strip())
        for e in (first_e, last_e, affil_e, wiki_e):
            e.delete(0, END)
        refresh()

    def delete_selected():
        for item in tree.selection():
            db.delete_author(session, int(item))
        refresh()

    Button(addFrame, text="Add", bg=BTN_DARK, fg='white', font=FONT,
           relief='flat', cursor='hand2', command=add).place(relx=0.87, rely=0.28, relwidth=0.12, relheight=0.45)
    Button(root, text="Delete Selected", bg=BTN_DEL, fg='white', font=FONT,
           relief='flat', cursor='hand2', command=delete_selected).place(relx=0.3, rely=0.9, relwidth=0.2, relheight=0.07)
    _back_button(root, session)
