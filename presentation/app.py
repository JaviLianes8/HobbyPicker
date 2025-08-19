import tkinter as tk
from tkinter import ttk, messagebox, font
from functools import partial
from domain import use_cases
from presentation.widgets.styles import apply_style
from presentation.utils.theme_prefs import load_theme, save_theme
from presentation.utils.window_utils import WindowUtils
from presentation.widgets.simple_entry_dialog import SimpleEntryDialog
from presentation.widgets.roulette_canvas import RouletteCanvas

def start_app() -> None:
    """Launch the main HobbyPicker window."""
    root = tk.Tk()
    root.title("HobbyPicker")
    # Ajustar tamaño a la resolución actual de la pantalla
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    root.geometry(f"{screen_width}x{screen_height}")
    root.resizable(False, False)

    current_theme = tk.StringVar(value=load_theme())
    apply_style(root, theme=current_theme.get())

    menubar = tk.Menu(root)
    theme_menu = tk.Menu(menubar, tearoff=0)

    def set_theme(t: str) -> None:
        current_theme.set(t)
        apply_style(root, theme=t)
        style = ttk.Style(root)
        wheel.configure(bg=style.lookup("Surface.TFrame", "background"))
        canvas.configure(bg=style.lookup("TFrame", "background"))
        save_theme(t)

    theme_menu.add_radiobutton(
        label="Claro", variable=current_theme, value="light", command=lambda: set_theme("light")
    )
    theme_menu.add_radiobutton(
        label="Oscuro", variable=current_theme, value="dark", command=lambda: set_theme("dark")
    )
    theme_menu.add_radiobutton(
        label="Sistema", variable=current_theme, value="system", command=lambda: set_theme("system")
    )
    menubar.add_cascade(label="Tema", menu=theme_menu)
    root.config(menu=menubar)

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # --- Pestaña: ¿Qué hago hoy? ---
    frame_suggest = ttk.Frame(notebook, style="Surface.TFrame")
    notebook.add(frame_suggest, text="¿Qué hago hoy?")

    suggestion_label = ttk.Label(
        frame_suggest,
        text="Pulsa el botón para sugerencia",
        font=("Segoe UI", 40, "bold"),
        wraplength=screen_width - 200,
        justify="center",
    )

    suggestion_label.pack(pady=(40, 40))

    wheel_size = int(min(screen_width, screen_height) * 0.6)
    wheel = RouletteCanvas(frame_suggest, width=wheel_size, height=wheel_size)
    wheel.pack(pady=20)

    def refresh_wheel():
        data = [
            {"id": d[0], "name": d[1], "weight": d[2], "percentage": d[3]}
            for d in use_cases.get_activity_weights()
        ]
        wheel.draw(data)

    root.after(100, refresh_wheel)

    def _fit_label(event):
        """Shrink label font so text fits within its width."""
        widget = event.widget
        widget.config(wraplength=widget.winfo_width())
        if not hasattr(widget, "_dyn_font"):
            widget._dyn_font = font.Font(font=widget.cget("font"))
            widget.config(font=widget._dyn_font)
        fnt = widget._dyn_font
        words = widget.cget("text").split()
        longest = max(words, key=len) if words else ""
        size = fnt.cget("size")
        while size > 8 and fnt.measure(longest) > widget.winfo_width():
            size -= 1
            fnt.configure(size=size)

    current_item = {"id": None, "name": None}

    def suggest():
        result = use_cases.get_weighted_random_valid_activity()
        if not result:
            suggestion_label.config(text="No hay hobbies configurados. Ve a la pestaña de configuración.")
            return

        final_id, final_text = result
        current_item["id"] = final_id
        current_item["name"] = final_text

        wheel.spin_to(
            final_id,
            on_step=lambda _id, name: suggestion_label.config(
                text=f"¿Qué tal hacer: {name}?"
            ),
        )

    def accept():
        if current_item["id"]:
            use_cases.mark_item_as_done(current_item["id"])
            current_item["id"] = None
            current_item["name"] = None
            suggestion_label.config(text="Pulsa el botón para sugerencia")
            refresh_wheel()
            wheel.highlight(None)

    button_container = ttk.Frame(frame_suggest)
    button_container.pack(pady=(40, 60))

    ttk.Button(button_container, text="🎲 Sugerir hobby", command=suggest, style="Big.TButton", width=25).pack(pady=10)
    ttk.Button(button_container, text="✅ ¡Me gusta!", command=accept, style="Big.TButton", width=25).pack(pady=10)

    # --- Pestaña: Configurar gustos ---
    frame_config = ttk.Frame(notebook)
    notebook.add(frame_config, text="⚙️ Configurar gustos")

    main_config_layout = ttk.Frame(frame_config)
    main_config_layout.pack(fill="both", expand=True)

    canvas_bg = ttk.Style(root).lookup("TFrame", "background")
    canvas = tk.Canvas(main_config_layout, bg=canvas_bg, highlightthickness=0)
    scrollbar = ttk.Scrollbar(main_config_layout, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollable_frame = ttk.Frame(canvas)
    def update_scrollregion(e=None):
        canvas.configure(scrollregion=canvas.bbox("all"))
        canvas.itemconfig("inner_frame", width=canvas.winfo_width())

    scrollable_frame.bind("<Configure>", update_scrollregion)
    canvas.bind("<Configure>", update_scrollregion)

    canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", tags="inner_frame")

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    sticky_bottom = ttk.Frame(main_config_layout)
    sticky_bottom.pack(fill="x", side="bottom", pady=5)
    ttk.Button(sticky_bottom, text="➕ Añadir hobby", command=lambda: open_add_hobby_window()).pack()

    hobbies_container = scrollable_frame

    def refresh_listbox():
        refresh_wheel()
        for widget in hobbies_container.winfo_children():
            widget.destroy()
        for hobby in use_cases.get_all_hobbies():
            row = ttk.Frame(hobbies_container, style="Surface.TFrame")
            row.pack(fill="x", pady=4, padx=10)

            row.columnconfigure(0, weight=1)
            row.columnconfigure(1, weight=0)

            label = ttk.Label(row, text=hobby[1], anchor="w", style="Heading.TLabel", justify="left")
            label.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
            label.bind("<Configure>", _fit_label)

            button_frame = ttk.Frame(row, style="Surface.TFrame")
            button_frame.grid(row=0, column=1, sticky="e", padx=10, pady=8)

            ttk.Button(button_frame, text="ⓘ",
                    command=partial(open_edit_hobby_window, hobby[0], hobby[1])).pack(side="left", padx=2)
            ttk.Button(button_frame, text="🗑",
                    command=partial(confirm_delete_hobby, hobby[0], hobby[1])).pack(side="left", padx=2)

    def confirm_delete_hobby(hobby_id, hobby_name):
        if messagebox.askyesno("Eliminar", f"¿Eliminar hobby '{hobby_name}'? Esta acción es irreversible."):
            use_cases.delete_hobby(hobby_id)
            refresh_listbox()
            messagebox.showinfo("Eliminado", f"Hobby '{hobby_name}' eliminado.")

    def open_edit_hobby_window(hobby_id, hobby_name):
        edit_window = tk.Toplevel()
        apply_style(edit_window, theme=current_theme.get())
        edit_window.title(f"Editar: {hobby_name}")
        WindowUtils.center_window(edit_window, 400, 600)
        edit_window.minsize(400, 600)

        ttk.Label(edit_window, text="Subelementos:").pack(pady=5)
        items_frame = ttk.Frame(edit_window)
        items_frame.pack(fill="both", expand=True, pady=5)

        def refresh_items():
            for w in items_frame.winfo_children():
                w.destroy()
            for item in use_cases.get_subitems_for_hobby(hobby_id):
                row = ttk.Frame(items_frame, style="Surface.TFrame")
                row.pack(fill="x", pady=2, padx=10)

                label = ttk.Label(row, text=item[2], anchor="w", justify="left")
                label.pack(side="left", fill="x", expand=True)
                label.bind("<Configure>", _fit_label)

                def edit_subitem(subitem_id=item[0], current_name=item[2]):
                    
                    new_name = SimpleEntryDialog.ask(
                        parent=edit_window,
                        title="Editar subelemento",
                        prompt=f"Nuevo nombre para '{current_name}':",
                        initial_value=current_name,
                        theme=current_theme.get(),
                    )
                    if new_name and new_name.strip() != current_name:
                        use_cases.update_subitem(subitem_id, new_name.strip())
                        refresh_items()

                ttk.Button(row, text="🗑", width=3, command=lambda: delete_item(item[0], item[2])).pack(side="right", padx=2)
                ttk.Button(row, text="ⓘ", width=3, command=edit_subitem).pack(side="right")

        def delete_item(item_id, name):
            if messagebox.askyesno("Eliminar", f"¿Eliminar subelemento '{name}'?"):
                use_cases.delete_subitem(item_id)
                refresh_items()

        def add_subitem():
            new_item = SimpleEntryDialog.ask(
                parent=edit_window,
                title="Nuevo subelemento",
                prompt="Introduce nuevo:",
                theme=current_theme.get(),
            )
            if new_item:
                use_cases.add_subitem_to_hobby(hobby_id, new_item.strip())
                refresh_items()

        ttk.Button(edit_window, text="Añadir subelemento", command=add_subitem).pack(pady=10)
        refresh_items()

    def open_add_hobby_window():
        def save_hobby():
            name = hobby_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Debes introducir un título.")
                return
            hobby_id = use_cases.create_hobby(name)
            sub = SimpleEntryDialog.ask(
                parent=add_window,
                title="Subelemento",
                prompt="Introduce un elemento relacionado:",
                theme=current_theme.get(),
            )
            while sub:
                use_cases.add_subitem_to_hobby(hobby_id, sub.strip())
                sub = SimpleEntryDialog.ask(
                    parent=add_window,
                    title="Otro más?",
                    prompt="Introduce otro (o cancelar para terminar):",
                    theme=current_theme.get(),
                )
            add_window.destroy()
            refresh_listbox()

        add_window = tk.Toplevel(root)
        add_window.title("Añadir nuevo hobby")
        WindowUtils.center_window(add_window, 500, 200)
        add_window.minsize(500, 200)
        apply_style(add_window, theme=current_theme.get())
        ttk.Label(add_window, text="Título del hobby:").pack(pady=5)
        hobby_entry = ttk.Entry(add_window, width=40)
        hobby_entry.pack(pady=5)
        ttk.Button(add_window, text="Guardar", command=save_hobby).pack(pady=10)

    refresh_listbox()
    root.mainloop()
