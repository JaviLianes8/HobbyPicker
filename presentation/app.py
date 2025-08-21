import tkinter as tk
from tkinter import messagebox, ttk
from functools import partial
from domain import use_cases
from presentation.widgets.styles import apply_style, get_color
from presentation.utils.window_utils import WindowUtils
from presentation.widgets.simple_entry_dialog import SimpleEntryDialog


def start_app() -> None:
    """Launch the main HobbyPicker window."""
    root = tk.Tk()
    root.state("zoomed")
    WindowUtils.center_window(root, 1240, 600)
    root.title("HobbyPicker")
    root.minsize(1240, 600)

    apply_style(root, "system")
    canvas = None  # se asigna más tarde
    separator = None  # línea divisoria asignada después
    animation_canvas = None  # zona de animación para las sugerencias

    # --- Notebook principal ---
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # --- Menú Tema (desplegable) ---
    theme_options = {"Sistema": "system", "Claro": "light", "Oscuro": "dark"}
    theme_var = tk.StringVar(value="Sistema")

    def change_theme_to(value: str) -> None:
        apply_style(root, theme_options[value])
        if canvas is not None:
            canvas.configure(bg=get_color("surface"))
        if animation_canvas is not None:
            animation_canvas.configure(bg=get_color("surface"))

    menubar = tk.Menu(root)
    theme_menu = tk.Menu(menubar, tearoff=0)
    for label in theme_options.keys():
        theme_menu.add_radiobutton(
            label=label,
            variable=theme_var,
            value=label,
            command=lambda lbl=label: change_theme_to(lbl),
        )
    menubar.add_cascade(label="Tema", menu=theme_menu)
    root.config(menu=menubar)
    change_theme_to(theme_var.get())  # tema inicial

    # --- Pestaña: ¿Qué hago hoy? ---
    frame_suggest = ttk.Frame(notebook, style="Surface.TFrame")
    notebook.add(frame_suggest, text="¿Qué hago hoy?")

    frame_suggest.columnconfigure(0, weight=1)
    frame_suggest.columnconfigure(1, weight=0)
    frame_suggest.columnconfigure(2, weight=0)
    frame_suggest.rowconfigure(0, weight=1)

    content_frame = ttk.Frame(frame_suggest, style="Surface.TFrame")
    content_frame.grid(row=0, column=0, sticky="nsew")

    separator = ttk.Separator(frame_suggest, orient="vertical")
    separator.grid(row=0, column=1, sticky="ns", padx=5)

    table_frame = ttk.Frame(frame_suggest, style="Surface.TFrame", width=660)
    table_frame.grid(row=0, column=2, sticky="nsew", padx=10)
    table_frame.grid_propagate(False)
    table_frame.rowconfigure(0, weight=1)
    table_frame.columnconfigure(0, weight=1)

    prob_table = ttk.Treeview(
        table_frame,
        columns=("activity", "percent"),
        show="headings",
        style="Probability.Treeview",
    )
    prob_table.heading("activity", text="Actividad", anchor="center")
    prob_table.heading("percent", text="%", anchor="center")
    prob_table.column("activity", width=480, anchor="center")
    prob_table.column("percent", width=180, anchor="center")

    v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=prob_table.yview)
    prob_table.configure(yscrollcommand=v_scroll.set)

    prob_table.grid(row=0, column=0, sticky="nsew")
    v_scroll.grid(row=0, column=1, sticky="ns")

    def refresh_probabilities():
        for row in prob_table.get_children():
            prob_table.delete(row)
        for name, prob in use_cases.get_activity_probabilities():
            prob_table.insert("", "end", values=(name, f"{prob*100:.1f}%"))

    refresh_probabilities()

    suggestion_label = ttk.Label(
        content_frame,
        text="Pulsa el botón para sugerencia",
        font=("Segoe UI", 28, "bold"),
        wraplength=500,
        justify="center",
        style="Surface.TLabel",
    )
    suggestion_label.pack(pady=(60, 40), expand=True)

    animation_canvas = tk.Canvas(
        content_frame,
        width=540,
        height=80,
        bg=get_color("surface"),
        highlightthickness=0,
    )

    current_activity = {"id": None, "name": None, "is_subitem": False}

    def suggest():
        result = use_cases.get_weighted_random_valid_activity()
        if not result:
            suggestion_label.config(
                text="No hay hobbies configurados. Ve a la pestaña de configuración."
            )
            return

        final_id, final_text, is_sub = result
        current_activity["id"] = final_id
        current_activity["name"] = final_text
        current_activity["is_subitem"] = is_sub

        options = []
        for _ in range(30):
            alt = use_cases.get_weighted_random_valid_activity()
            if alt:
                options.append(alt[1])
        options += [final_text, ""]

        animation_canvas.delete("all")
        box_w, box_h = 180, 60
        for i, text in enumerate(options):
            x = i * box_w
            animation_canvas.create_rectangle(
                x,
                0,
                x + box_w,
                box_h,
                fill=get_color("light"),
                outline="",
                tags=("item",),
            )
            animation_canvas.create_text(
                x + box_w / 2,
                box_h / 2,
                text=text,
                width=box_w - 10,
                fill=get_color("text"),
                tags=("item",),
            )
        animation_canvas.create_rectangle(
            box_w,
            0,
            box_w * 2,
            box_h,
            outline=get_color("primary"),
            width=3,
        )

        suggestion_label.pack_forget()
        animation_canvas.pack(pady=(60, 40))

        total_shift = (len(options) - 3) * box_w

        def roll(step=0, speed=25):
            if step < total_shift:
                animation_canvas.move("item", -speed, 0)
                step += speed
                if total_shift - step < box_w * 2 and speed > 2:
                    speed -= 1
                root.after(20, lambda: roll(step, speed))
            else:
                animation_canvas.move("item", -(total_shift - step), 0)
                animation_canvas.after(300, finish)

        def finish():
            animation_canvas.pack_forget()
            suggestion_label.config(text=f"¿Qué tal hacer: {final_text}?")
            suggestion_label.pack(pady=(60, 40), expand=True)

        roll()

    def accept():
        if current_activity["id"]:
            use_cases.mark_activity_as_done(
                current_activity["id"], current_activity["is_subitem"]
            )
            current_activity["id"] = None
            current_activity["name"] = None
            current_activity["is_subitem"] = False
            suggestion_label.config(text="Pulsa el botón para sugerencia")
            refresh_probabilities()

    button_container = ttk.Frame(content_frame, style="Surface.TFrame")
    button_container.pack(pady=(20, 40))

    ttk.Button(
        button_container,
        text="🎲 Sugerir hobby",
        command=suggest,
        style="Big.TButton",
        width=20,
    ).pack(pady=10)

    ttk.Button(
        button_container,
        text="✅ ¡Me gusta!",
        command=accept,
        style="Big.TButton",
        width=20,
    ).pack(pady=10)

    def on_tab_change(event):
        if notebook.index("current") == 0:
            refresh_probabilities()

    notebook.bind("<<NotebookTabChanged>>", on_tab_change)

    # --- Pestaña: Configurar hobbies ---
    frame_config = ttk.Frame(notebook, style="Surface.TFrame")
    notebook.add(frame_config, text="⚙️ Configurar hobbies")

    main_config_layout = ttk.Frame(frame_config, style="Surface.TFrame")
    main_config_layout.pack(fill="both", expand=True)

    canvas = tk.Canvas(
        main_config_layout, bg=get_color("surface"), highlightthickness=0
    )
    scrollbar = ttk.Scrollbar(
        main_config_layout, orient="vertical", command=canvas.yview
    )
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollable_frame = ttk.Frame(canvas, style="Surface.TFrame")

    def update_scrollregion(e=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig("inner_frame", width=canvas.winfo_width())

    scrollable_frame.bind("<Configure>", update_scrollregion)
    canvas.bind("<Configure>", update_scrollregion)

    canvas.create_window(
        (0, 0), window=scrollable_frame, anchor="nw", tags="inner_frame"
    )

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    sticky_bottom = ttk.Frame(main_config_layout, style="Surface.TFrame")
    sticky_bottom.pack(fill="x", side="bottom", pady=5)
    ttk.Button(
        sticky_bottom, text="➕ Añadir hobby", command=lambda: open_add_hobby_window()
    ).pack()

    hobbies_container = scrollable_frame

    def refresh_listbox():
        for widget in hobbies_container.winfo_children():
            widget.destroy()
        for hobby in use_cases.get_all_hobbies():
            row = ttk.Frame(
                hobbies_container, style="Outlined.Surface.TFrame", padding=5
            )
            row.pack(fill="x", pady=4, padx=10)

            row.columnconfigure(0, weight=1)
            row.columnconfigure(1, weight=0)

            label = ttk.Label(
                row, text=hobby[1], anchor="w", style="Heading.Surface.TLabel"
            )
            label.grid(row=0, column=0, sticky="w", padx=10, pady=8)

            button_frame = ttk.Frame(row, style="Surface.TFrame")
            button_frame.grid(row=0, column=1, sticky="e", padx=10, pady=8)

            ttk.Button(
                button_frame,
                text="ⓘ",
                command=partial(open_edit_hobby_window, hobby[0], hobby[1]),
            ).pack(side="left", padx=2)

            ttk.Button(
                button_frame,
                text="🗑",
                command=partial(confirm_delete_hobby, hobby[0], hobby[1]),
            ).pack(side="left", padx=2)

    def confirm_delete_hobby(hobby_id, hobby_name):
        if messagebox.askyesno(
            "Eliminar", f"¿Eliminar hobby '{hobby_name}'? Esta acción es irreversible."
        ):
            use_cases.delete_hobby(hobby_id)
            refresh_listbox()
            messagebox.showinfo("Eliminado", f"Hobby '{hobby_name}' eliminado.")

    def open_edit_hobby_window(hobby_id, hobby_name):
        edit_window = tk.Toplevel()
        apply_style(edit_window)
        edit_window.title(f"Editar: {hobby_name}")
        WindowUtils.center_window(edit_window, 400, 600)
        edit_window.minsize(400, 600)

        ttk.Label(edit_window, text="Subelementos:").pack(pady=5)
        items_frame = ttk.Frame(edit_window, style="Surface.TFrame")
        items_frame.pack(fill="both", expand=True, pady=5)

        def refresh_items():
            for w in items_frame.winfo_children():
                w.destroy()
            for item in use_cases.get_subitems_for_hobby(hobby_id):
                row = ttk.Frame(
                    items_frame, style="Outlined.Surface.TFrame", padding=5
                )
                row.pack(fill="x", pady=2, padx=10)

                label = ttk.Label(row, text=item[2], anchor="w", style="Surface.TLabel")
                label.pack(side="left", expand=True)

                def edit_subitem(subitem_id=item[0], current_name=item[2]):
                    new_name = SimpleEntryDialog.ask(
                        parent=edit_window,
                        title="Editar subelemento",
                        prompt=f"Nuevo nombre para '{current_name}':",
                        initial_value=current_name,
                    )
                    if new_name and new_name.strip() != current_name:
                        use_cases.update_subitem(subitem_id, new_name.strip())
                        refresh_items()

                ttk.Button(
                    row,
                    text="🗑",
                    width=3,
                    command=lambda: delete_item(item[0], item[2]),
                ).pack(side="right", padx=2)
                ttk.Button(
                    row, text="ⓘ", width=3, command=edit_subitem
                ).pack(side="right")

        def delete_item(item_id, name):
            if messagebox.askyesno("Eliminar", f"¿Eliminar subelemento '{name}'?"):
                use_cases.delete_subitem(item_id)
                refresh_items()

        def add_subitem():
            new_item = SimpleEntryDialog.ask(
                parent=edit_window, title="Nuevo subelemento", prompt="Introduce nuevo:"
            )
            if new_item:
                use_cases.add_subitem_to_hobby(hobby_id, new_item.strip())
                refresh_items()

        ttk.Button(
            edit_window, text="Añadir subelemento", command=add_subitem
        ).pack(pady=10)
        refresh_items()

    def open_add_hobby_window():
        def save_hobby():
            name = hobby_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Debes introducir un título.")
                return
            hobby_id = use_cases.create_hobby(name)
            sub = SimpleEntryDialog.ask(
                parent=add_window, title="Subelemento", prompt="Introduce un elemento relacionado:"
            )
            while sub:
                use_cases.add_subitem_to_hobby(hobby_id, sub.strip())
                sub = SimpleEntryDialog.ask(
                    parent=add_window,
                    title="Otro más?",
                    prompt="Introduce otro (o cancelar para terminar):",
                )
            add_window.destroy()
            refresh_listbox()

        add_window = tk.Toplevel(root)
        apply_style(add_window)
        add_window.title("Añadir nuevo hobby")
        WindowUtils.center_window(add_window, 500, 200)
        add_window.minsize(500, 200)
        ttk.Label(add_window, text="Título del hobby:").pack(pady=5)
        hobby_entry = ttk.Entry(add_window, width=40)
        hobby_entry.pack(pady=5)
        ttk.Button(add_window, text="Guardar", command=save_hobby).pack(pady=10)

    refresh_listbox()
    root.mainloop()
