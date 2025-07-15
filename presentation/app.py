import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from functools import partial
from domain import use_cases
from presentation.widgets.styles import apply_style

def start_app():
    root = tk.Tk()
    root.title("HobbyPicker")
    root.geometry("800x600")
    root.minsize(800, 600)
    apply_style()

    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # --- Pestaña: ¿Qué hago hoy? ---
    frame_suggest = ttk.Frame(notebook)
    notebook.add(frame_suggest, text="¿Qué hago hoy?")

    suggestion_label = tk.Label(frame_suggest, text="Pulsa el botón para sugerencia", font=("Arial", 14), wraplength=500)
    suggestion_label.pack(pady=20)

    current_activity = {"id": None, "name": None}

    def suggest():
        result = use_cases.get_weighted_random_valid_activity()
        if not result:
            suggestion_label.config(text="No hay hobbies configurados. Ve a la pestaña de configuración.")
            return

        final_id, final_text = result
        current_activity["id"] = final_id
        current_activity["name"] = final_text

        options = []
        for _ in range(30):
            alt = use_cases.get_weighted_random_valid_activity()
            if alt:
                options.append(alt[1])
        options.append(final_text)

        def animate(i=0):
            if i < len(options):
                suggestion_label.config(text=f"¿Qué tal hacer: {options[i]}?")
                root.after(100, lambda: animate(i + 1))
            else:
                suggestion_label.config(text=f"¿Qué tal hacer: {final_text}?")

        animate()

    def accept():
        if current_activity["id"]:
            use_cases.mark_activity_as_done(current_activity["id"])
            current_activity["id"] = None
            current_activity["name"] = None
            suggestion_label.config(text="Pulsa el botón para sugerencia")

    tk.Button(frame_suggest, text="Sugerir hobby", command=suggest).pack(pady=10)
    tk.Button(frame_suggest, text="¡Me gusta!", command=accept).pack(pady=10)

    # --- Pestaña: Configurar gustos ---
    frame_config = ttk.Frame(notebook)
    notebook.add(frame_config, text="⚙️ Configurar gustos")

    # Layout principal con scroll y botón fijo
    main_config_layout = tk.Frame(frame_config, bg="#f6f9fc")
    main_config_layout.pack(fill="both", expand=True)

    # Scrollable area
    canvas = tk.Canvas(main_config_layout, bg="#f6f9fc", highlightthickness=0)
    scrollbar = ttk.Scrollbar(main_config_layout, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollable_frame = tk.Frame(canvas, bg="#f6f9fc")
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Botón fijo abajo
    sticky_bottom = tk.Frame(main_config_layout, bg="#f6f9fc")
    sticky_bottom.pack(fill="x", side="bottom", pady=5)
    ttk.Button(sticky_bottom, text="➕ Añadir hobby", command=lambda: open_add_hobby_window()).pack()

    # --- Hobbies container ---
    hobbies_container = scrollable_frame

    def refresh_listbox():
        for widget in hobbies_container.winfo_children():
            widget.destroy()
        for hobby in use_cases.get_all_hobbies():
            row = tk.Frame(hobbies_container, bg="#ffffff", bd=1, relief="solid")
            row.pack(fill="x", pady=4, padx=10)

            label = tk.Label(row, text=hobby[1], anchor="w", bg="#ffffff", font=("Segoe UI", 11))
            label.pack(side="left", fill="x", expand=True, padx=10, pady=8)

            button_frame = tk.Frame(row, bg="#ffffff")
            button_frame.pack(side="right", padx=10, pady=8)

            ttk.Button(button_frame, text="✏️", width=3,
                    command=partial(open_edit_hobby_window, hobby[0], hobby[1])).pack(side="left", padx=2)
            ttk.Button(button_frame, text="🗑", width=3,
                    command=partial(confirm_delete_hobby, hobby[0], hobby[1])).pack(side="left", padx=2)

    def confirm_delete_hobby(hobby_id, hobby_name):
        if messagebox.askyesno("Eliminar", f"¿Eliminar hobby '{hobby_name}'? Esta acción es irreversible."):
            use_cases.delete_hobby(hobby_id)
            refresh_listbox()
            messagebox.showinfo("Eliminado", f"Hobby '{hobby_name}' eliminado.")

    def open_edit_hobby_window(hobby_id, hobby_name):
        edit_window = tk.Toplevel()
        edit_window.title(f"Editar: {hobby_name}")
        edit_window.geometry("400x400")

        tk.Label(edit_window, text="Subelementos:").pack(pady=5)
        items_frame = tk.Frame(edit_window)
        items_frame.pack(fill="both", expand=True, pady=5)

        def refresh_items():
            for w in items_frame.winfo_children():
                w.destroy()
            for item in use_cases.get_subitems_for_hobby(hobby_id):
                row = tk.Frame(items_frame)
                row.pack(fill="x", pady=2, padx=10)

                name_var = tk.StringVar(value=item[2])
                label = tk.Label(row, textvariable=name_var, anchor="w")
                label.pack(side="left", expand=True)

                def edit_subitem(subitem_id=item[0], current_name=item[2]):
                    new_name = simpledialog.askstring("Editar subelemento", f"Nuevo nombre para '{current_name}':", initialvalue=current_name)
                    if new_name and new_name.strip() != current_name:
                        use_cases.update_subitem(subitem_id, new_name.strip())
                        refresh_items()

                tk.Button(row, text="✏️", width=3, command=edit_subitem).pack(side="right", padx=2)
                tk.Button(row, text="🗑", width=3, command=lambda: delete_item(item[0], item[2])).pack(side="right")

        def delete_item(item_id, name):
            if messagebox.askyesno("Eliminar", f"¿Eliminar subelemento '{name}'?"):
                use_cases.delete_subitem(item_id)
                refresh_items()

        def add_subitem():
            new_item = simpledialog.askstring("Nuevo subelemento", "Introduce nuevo:")
            if new_item:
                use_cases.add_subitem_to_hobby(hobby_id, new_item.strip())
                refresh_items()

        tk.Button(edit_window, text="Añadir subelemento", command=add_subitem).pack(pady=10)
        refresh_items()

    def open_add_hobby_window():
        def save_hobby():
            name = hobby_entry.get().strip()
            if not name:
                messagebox.showerror("Error", "Debes introducir un título.")
                return
            hobby_id = use_cases.create_hobby(name)
            sub = simpledialog.askstring("Subelemento", "Introduce un elemento relacionado (libro, actividad, etc.):")
            while sub:
                use_cases.add_subitem_to_hobby(hobby_id, sub.strip())
                sub = simpledialog.askstring("Otro más?", "Introduce otro (o cancelar para terminar):")
            add_window.destroy()
            refresh_listbox()

        add_window = tk.Toplevel(root)
        add_window.title("Añadir nuevo hobby")
        tk.Label(add_window, text="Título del hobby:").pack(pady=5)
        hobby_entry = tk.Entry(add_window, width=40)
        hobby_entry.pack(pady=5)
        tk.Button(add_window, text="Guardar", command=save_hobby).pack(pady=10)

    refresh_listbox()
    root.mainloop()