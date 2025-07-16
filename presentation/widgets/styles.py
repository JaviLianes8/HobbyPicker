from tkinter import ttk

def apply_style(master: ttk.Widget | None = None) -> None:
    """Apply the application's visual theme."""
    style = ttk.Style(master)
    style.theme_use("clam")

    # 📘 Paleta base
    primary = "#4A90E2"
    primary_hover = "#3A78C2"
    background = "#f6f9fc"
    light = "#e0e0e0"
    text = "#333333"

    base_font = ("Segoe UI", 10)
    bold_font = ("Segoe UI", 10, "bold")

    # 📚 General
    style.configure(".", background=background, foreground=text, font=(base_font))
    style.configure("TFrame", background=background)
    style.configure("TLabel", background=background, font=("Segoe UI", 11))
    style.configure("TEntry", relief="flat", padding=6)
    style.map("TEntry", foreground=[("focus", text)])

    # 🧩 Notebook (tabs)
    style.configure("TNotebook", background=background, padding=10)
    style.configure("TNotebook.Tab", background=light, foreground=text, font=bold_font, padding=(12, 6))
    style.map("TNotebook.Tab", background=[("selected", background)], foreground=[("selected", primary)])

    # 🔘 Botones
    style.configure("TButton",
        background=primary,
        foreground="white",
        font=bold_font,
        padding=8,
        relief="flat",
        borderwidth=0
    )
    style.map("TButton",
        background=[("active", primary_hover), ("disabled", light)],
        relief=[("pressed", "sunken")]
    )

    # 📃 Listbox (manual styling via widget config en app)
    # No se aplica por Style, se estiliza en el código si quieres (scrollbar, colors...)

    # 📋 Combobox (si lo usas en el futuro)
    style.configure("TCombobox",
        fieldbackground="white",
        background=light,
        padding=6
    )

    # ✅ Checkbutton y radiobutton
    style.configure("TRadiobutton", background=background, padding=5)
    style.configure("TCheckbutton", background=background, padding=5)

    # 🧾 Scrollbar (si lo usas)
    style.configure("Vertical.TScrollbar", gripcount=0,
        background=light, darkcolor=light, lightcolor=light,
        troughcolor=background, bordercolor=light, arrowcolor=primary
    )

    # 🪟 Toplevel (ventanas nuevas)
    style.configure("Toplevel", background=background)

    # 🖊 Tooltip idea futura
    # style.configure("ToolTip", background="#ffffe0", foreground="#000000", relief="solid", borderwidth=1)

    # 🎨 Padding global (manual en el layout también)
    # Puedes meter `.pack(padx=10, pady=6)` en tus componentes visuales para más coherencia