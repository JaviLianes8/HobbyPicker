import tkinter as tk
from tkinter import ttk


def apply_style(master: ttk.Widget | None = None, theme: str = "light") -> None:
    """Apply a modern, professional theme to all Tk widgets.

    Args:
        master: Optional widget used to scope the style.
        theme: Either ``"light"`` or ``"dark"``.
    """
    style = ttk.Style(master)
    style.theme_use("clam")

    if theme == "dark":
        primary = "#0A84FF"
        primary_hover = "#0060DF"
        background = "#121212"
        surface = "#1E1E1E"
        light = "#2C2C2C"
        text = "#F5F5F5"
        subtle = "#AAAAAA"
    else:  # light theme
        primary = "#0078D4"
        primary_hover = "#0063B1"
        background = "#E3F2FD"  # light blue background
        surface = "#FFFFFF"
        light = "#BBDEFB"
        text = "#1F2A36"
        subtle = "#6B7785"

    base_font = ("Helvetica", 11)
    bold_font = ("Helvetica", 11, "bold")
    large_font = ("Helvetica", 13, "bold")

    # 📚 Base widgets
    style.configure(".", background=background, foreground=text, font=(base_font))
    style.configure("TFrame", background=background)
    style.configure("Surface.TFrame", background=surface, relief="ridge", borderwidth=1)
    style.configure("TLabel", background=background, font=base_font, foreground=text)
    style.configure("Heading.TLabel", font=large_font)
    style.configure("TEntry", relief="flat", padding=6)
    style.map("TEntry", foreground=[("focus", text)])

    # 🧩 Notebook (tabs)
    style.configure("TNotebook", background=background, padding=10)
    style.configure("TNotebook.Tab", background=surface, foreground=subtle, font=bold_font, padding=(12, 6))
    style.map("TNotebook.Tab", background=[("selected", background)], foreground=[("selected", primary)])

    # 🔘 Buttons
    style.configure(
        "TButton",
        background=primary,
        foreground="white",
        font=bold_font,
        padding=8,
        relief="flat",
        borderwidth=0,
    )
    style.map(
        "TButton",
        background=[("active", primary_hover), ("disabled", light)],
        relief=[("pressed", "sunken")],
    )
    style.configure("Big.TButton", font=("Helvetica", 18, "bold"), padding=(20, 16))

    # 📃 Listbox (manual styling via widget config en app)
    # No se aplica por Style, se estiliza en el código si quieres (scrollbar, colors...)

    # 📋 Combobox (si lo usas en el futuro)
    style.configure(
        "TCombobox",
        fieldbackground="white",
        background=light,
        padding=6,
    )

    # ✅ Checkbutton y radiobutton
    style.configure("TRadiobutton", background=background, padding=5)
    style.configure("TCheckbutton", background=background, padding=5)

    # 🧾 Scrollbar (si lo usas)
    style.configure(
        "Vertical.TScrollbar",
        gripcount=0,
        background=light,
        darkcolor=light,
        lightcolor=light,
        troughcolor=background,
        bordercolor=light,
        arrowcolor=primary,
    )

    # 🪟 Toplevel (ventanas nuevas)
    style.configure("Toplevel", background=background)

    if master is not None:
        try:
            master.configure(bg=background)
        except tk.TclError:  # master may be a ttk widget lacking bg option
            pass

    # 🖊 Tooltip idea futura
    # style.configure("ToolTip", background="#ffffe0", foreground="#000000", relief="solid", borderwidth=1)

    # 🎨 Padding global (manual en el layout también)
    # Puedes meter `.pack(padx=10, pady=6)` en tus componentes visuales para más coherencia