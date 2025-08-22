import tkinter as tk
from tkinter import ttk, messagebox
from functools import partial
from domain import use_cases
from presentation.widgets.styles import get_color, apply_style
from presentation.widgets.simple_entry_dialog import SimpleEntryDialog
from presentation.utils.window_utils import WindowUtils


def create_config_tab(root, notebook, tr, prob_table, is_steam_game_label,
                      refresh_probabilities, show_game_popup, build_activity_caches):
    frame = ttk.Frame(notebook, style="Surface.TFrame")
    notebook.add(frame, text=tr("tab_config"))
    layout = ttk.Frame(frame, style="Surface.TFrame")
    layout.pack(fill="both", expand=True)
    canvas = tk.Canvas(layout, bg=get_color("surface"), highlightthickness=0)
    scrollbar = ttk.Scrollbar(layout, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollable = ttk.Frame(canvas, style="Surface.TFrame")
    canvas.create_window((0, 0), window=scrollable, anchor="nw", tags="inner_frame")

    def update_scroll(_=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig("inner_frame", width=canvas.winfo_width())
    scrollable.bind("<Configure>", update_scroll)
    canvas.bind("<Configure>", update_scroll)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    add_hobby_btn = ttk.Button(layout, text=tr("add_hobby"))
    add_hobby_btn.place(relx=0.0, rely=1.0, anchor="sw", x=20, y=-20)

    hobbies_container = scrollable

    def refresh_listbox():
        for w in hobbies_container.winfo_children():
            w.destroy()
        for hobby in use_cases.get_all_hobbies():
            row = ttk.Frame(hobbies_container, style="Outlined.Surface.TFrame", padding=5)
            row.pack(fill="x", pady=4, padx=10)
            row.columnconfigure(0, weight=1)
            ttk.Label(row, text=hobby[1], anchor="w", style="Heading.Surface.TLabel").grid(row=0, column=0, sticky="w", padx=10, pady=8)
            btn_frame = ttk.Frame(row, style="Surface.TFrame")
            btn_frame.grid(row=0, column=1, sticky="e", padx=10, pady=8)
            ttk.Button(btn_frame, text="ⓘ", command=partial(open_edit_hobby_window, hobby[0], hobby[1])).pack(side="left", padx=2)
            ttk.Button(btn_frame, text="🗑", command=partial(confirm_delete_hobby, hobby[0], hobby[1])).pack(side="left", padx=2)

    def confirm_delete_hobby(hobby_id, hobby_name):
        if messagebox.askyesno(tr("delete"), tr("delete_hobby_confirm").format(name=hobby_name)):
            use_cases.delete_hobby(hobby_id)
            refresh_listbox()
            build_activity_caches()
            messagebox.showinfo(tr("deleted"), tr("hobby_deleted").format(name=hobby_name))

    def on_prob_table_click(event):
        region = prob_table.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = prob_table.identify_column(event.x)
        row_id = prob_table.identify_row(event.y)
        if not row_id:
            return
        name = prob_table.item(row_id, "values")[0]
        if column == "#5":
            if row_id.startswith("h"):
                confirm_delete_hobby(int(row_id[1:]), name)
            elif row_id.startswith("s") and messagebox.askyesno(tr("delete"), tr("delete_subitem_confirm").format(name=name)):
                use_cases.delete_subitem(int(row_id[1:]))
                build_activity_caches()
                refresh_probabilities()
        elif column == "#3":
            if row_id.startswith("h"):
                open_edit_hobby_window(int(row_id[1:]), name)
            elif row_id.startswith("s"):
                new_name = SimpleEntryDialog.ask(parent=root, title=tr("edit_subitem_title"), prompt=tr("new_name_prompt").format(name=name), initial_value=name)
                if new_name:
                    use_cases.update_subitem(int(row_id[1:]), new_name.strip())
                    build_activity_caches()
                    refresh_probabilities()
        elif column == "#4" and row_id.startswith("s") and is_steam_game_label(name):
            show_game_popup(name.split(" + ", 1)[1])

    prob_table.bind("<Button-1>", on_prob_table_click)

    def open_edit_hobby_window(hobby_id, hobby_name):
        win = tk.Toplevel(root)
        apply_style(win)
        win.title(tr("edit_hobby_title").format(name=hobby_name))
        WindowUtils.center_window(win, 600, 600)
        win.minsize(600, 600)
        ttk.Label(win, text=tr("subitems")).pack(pady=5)
        items_canvas = tk.Canvas(win, bg=get_color("surface"), highlightthickness=0)
        items_scroll = ttk.Scrollbar(win, orient="vertical", command=items_canvas.yview)
        items_canvas.configure(yscrollcommand=items_scroll.set)
        items_canvas.pack(side="left", fill="both", expand=True, pady=5)
        items_scroll.pack(side="right", fill="y")
        items_frame = ttk.Frame(items_canvas, style="Surface.TFrame")
        items_canvas.create_window((0, 0), window=items_frame, anchor="nw", tags="inner_frame")

        def update_items_scroll(_=None):
            items_canvas.configure(scrollregion=items_canvas.bbox("all"))
            items_canvas.itemconfig("inner_frame", width=items_canvas.winfo_width())
        items_frame.bind("<Configure>", update_items_scroll)
        items_canvas.bind("<Configure>", update_items_scroll)

        def refresh_items():
            for w in items_frame.winfo_children():
                w.destroy()
            for item in use_cases.get_subitems_for_hobby(hobby_id):
                row = ttk.Frame(items_frame, style="Outlined.Surface.TFrame", padding=5)
                row.pack(fill="x", pady=2, padx=10)
                ttk.Label(row, text=item[2], anchor="w", style="Surface.TLabel").pack(side="left", expand=True)

                def edit_subitem(subitem_id=item[0], current=item[2]):
                    new_name = SimpleEntryDialog.ask(parent=win, title=tr("edit_subitem_title"), prompt=tr("new_name_prompt").format(name=current), initial_value=current)
                    if new_name and new_name.strip() != current:
                        use_cases.update_subitem(subitem_id, new_name.strip())
                        refresh_items()
                        build_activity_caches()

                ttk.Button(row, text="🗑", width=3, command=lambda i=item[0], n=item[2]: delete_item(i, n)).pack(side="right", padx=2)
                ttk.Button(row, text="ⓘ", width=3, command=edit_subitem).pack(side="right")

        def delete_item(item_id, name):
            if messagebox.askyesno(tr("delete"), tr("delete_subitem_confirm").format(name=name)):
                use_cases.delete_subitem(item_id)
                refresh_items()
                build_activity_caches()

        def add_subitem():
            new_item = SimpleEntryDialog.ask(parent=win, title=tr("new_subitem_title"), prompt=tr("new_subitem_prompt"))
            if new_item:
                use_cases.add_subitem_to_hobby(hobby_id, new_item.strip())
                refresh_items()
                build_activity_caches()

        ttk.Button(win, text=tr("add_subitem_btn"), command=add_subitem).place(relx=0.0, rely=1.0, anchor="sw", x=20, y=-20)
        refresh_items()

    def open_add_hobby_window():
        def save_hobby():
            name = hobby_entry.get().strip()
            if not name:
                messagebox.showerror(tr("error"), tr("need_title"))
                return
            hobby_id = use_cases.create_hobby(name)
            sub = SimpleEntryDialog.ask(parent=add_window, title=tr("subitem_title"), prompt=tr("subitem_prompt"))
            while sub:
                use_cases.add_subitem_to_hobby(hobby_id, sub.strip())
                sub = SimpleEntryDialog.ask(parent=add_window, title=tr("another_title"), prompt=tr("another_prompt"))
            build_activity_caches()
            add_window.destroy()
            refresh_listbox()

        add_window = tk.Toplevel(root)
        apply_style(add_window)
        add_window.title(tr("add_hobby_window_title"))
        WindowUtils.center_window(add_window, 500, 200)
        add_window.minsize(500, 200)
        ttk.Label(add_window, text=tr("hobby_title_label")).pack(pady=5)
        hobby_entry = ttk.Entry(add_window, width=40)
        hobby_entry.pack(pady=5)
        ttk.Button(add_window, text=tr("save"), command=save_hobby).pack(pady=10)

    add_hobby_btn.configure(command=open_add_hobby_window)
    refresh_listbox()
    return refresh_listbox
