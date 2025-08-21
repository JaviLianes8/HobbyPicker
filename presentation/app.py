import json
import locale
import os
import random
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlencode, urlparse, parse_qs, quote
from pathlib import Path
import xml.etree.ElementTree as ET
import requests
import tkinter as tk
from tkinter import messagebox, ttk
from functools import partial, lru_cache

from domain import use_cases
from presentation.widgets.styles import apply_style, get_color, add_button_hover
from presentation.utils.window_utils import WindowUtils
from presentation.widgets.simple_entry_dialog import SimpleEntryDialog




def start_app() -> None:
    """Launch the main HobbyPicker window."""
    root = tk.Tk()
    root.state("zoomed")
    WindowUtils.center_window(root, 1240, 600)
    root.title("HobbyPicker")
    root.minsize(1240, 600)

    config_path = Path.home() / ".hobbypicker.json"

    def load_settings() -> dict[str, str]:
        data = {"language": "system", "theme": "system"}
        try:
            if config_path.exists():
                with config_path.open("r", encoding="utf-8") as fh:
                    stored = json.load(fh)
                data.update({k: stored.get(k, v) for k, v in data.items()})
        except Exception:
            pass
        return data

    settings = load_settings()

    lang_var = tk.StringVar(value=settings["language"])
    theme_var = tk.StringVar(value=settings["theme"])

    include_games_var = tk.BooleanVar(value=True)
    installed_only_var = tk.BooleanVar(value=False)

    refresh_probabilities = None  # placeholder, defined after table creation

    def save_settings() -> None:
        try:
            with config_path.open("w", encoding="utf-8") as fh:
                json.dump({"language": lang_var.get(), "theme": theme_var.get()}, fh)
        except Exception:
            pass

    apply_style(root, theme_var.get())

    # --- Soporte de idiomas ---
    LANG_TEXT = {
        "es": {
            "tab_today": "¿Qué hago hoy?",
            "tab_config": "⚙️ Configurar hobbies",
            "prompt": "¿Qué tal?",
            "suggest_button": "🎲 Sugerir hobby",
            "accept_button": "✅ ¡Me gusta!",
            "another_button": "🎲 Otra sugerencia",
            "like_overlay": "✅ ¡Me gusta!",
            "no_hobbies": "No hay hobbies configurados. Ve a la pestaña de configuración.",
            "what_about": "¿Qué tal hacer: {}?",
            "menu_theme": "Tema",
            "menu_language": "Idioma",
            "theme_system": "Sistema",
            "theme_light": "Claro",
            "theme_dark": "Oscuro",
            "lang_system": "Sistema",
            "lang_spanish": "Español",
            "lang_english": "Inglés",
            "add_hobby": "➕ Añadir hobby",
            "col_activity": "Actividad",
            "col_percent": "%",
            "delete": "Eliminar",
            "delete_hobby_confirm": "¿Eliminar hobby '{name}'? Esta acción es irreversible.",
            "deleted": "Eliminado",
            "hobby_deleted": "Hobby '{name}' eliminado.",
            "subitems": "Subelementos:",
            "edit_hobby_title": "Editar: {name}",
            "edit_subitem_title": "Editar subelemento",
            "new_name_prompt": "Nuevo nombre para '{name}':",
            "delete_subitem_confirm": "¿Eliminar subelemento '{name}'?",
            "new_subitem_title": "Nuevo subelemento",
            "new_subitem_prompt": "Introduce nuevo:",
            "add_subitem_btn": "Añadir subelemento",
            "subitem_title": "Subelemento",
            "subitem_prompt": "Introduce un elemento relacionado:",
            "another_title": "¿Otro más?",
            "another_prompt": "Introduce otro (o cancelar para terminar):",
            "add_hobby_window_title": "Añadir nuevo hobby",
            "hobby_title_label": "Título del hobby:",
            "save": "Guardar",
            "error": "Error",
            "need_title": "Debes introducir un título.",
            "steam_import_confirm": "¿Importar juegos de Steam?",
            "steam_import_success": "Se importaron {count} juegos.",
            "steam_import_error": "No se pudo importar los juegos.",
            "steam_hobby_name": "Jugar",
            "steam_action_prompt": "¿Qué quieres hacer con '{name}'?",
            "steam_play": "Jugar juego",
            "steam_install": "Instalar juego",
            "steam_not_found": "No se encontró el juego en Steam.",
            "include_games": "Incluir juegos",
            "only_installed": "Solo juegos instalados",
        },
        "en": {
            "tab_today": "What should I do today?",
            "tab_config": "⚙️ Configure hobbies",
            "prompt": "How about?",
            "suggest_button": "🎲 Suggest hobby",
            "accept_button": "✅ I like it!",
            "another_button": "🎲 Another suggestion",
            "like_overlay": "✅ I like it!",
            "no_hobbies": "No hobbies configured. Go to the settings tab.",
            "what_about": "How about: {}?",
            "menu_theme": "Theme",
            "menu_language": "Language",
            "theme_system": "System",
            "theme_light": "Light",
            "theme_dark": "Dark",
            "lang_system": "System",
            "lang_spanish": "Spanish",
            "lang_english": "English",
            "add_hobby": "➕ Add hobby",
            "col_activity": "Activity",
            "col_percent": "%",
            "delete": "Delete",
            "delete_hobby_confirm": "Delete hobby '{name}'? This action cannot be undone.",
            "deleted": "Deleted",
            "hobby_deleted": "Hobby '{name}' deleted.",
            "subitems": "Subitems:",
            "edit_hobby_title": "Edit: {name}",
            "edit_subitem_title": "Edit subitem",
            "new_name_prompt": "New name for '{name}':",
            "delete_subitem_confirm": "Delete subitem '{name}'?",
            "new_subitem_title": "New subitem",
            "new_subitem_prompt": "Enter new:",
            "add_subitem_btn": "Add subitem",
            "subitem_title": "Subitem",
            "subitem_prompt": "Enter a related item:",
            "another_title": "Another one?",
            "another_prompt": "Enter another (or cancel to finish):",
            "add_hobby_window_title": "Add new hobby",
            "hobby_title_label": "Hobby title:",
            "save": "Save",
            "error": "Error",
            "need_title": "You must enter a title.",
            "steam_import_confirm": "Import Steam games?",
            "steam_import_success": "Imported {count} games.",
            "steam_import_error": "Could not import games.",
            "steam_hobby_name": "Play",
            "steam_action_prompt": "What do you want to do with '{name}'?",
            "steam_play": "Play game",
            "steam_install": "Install game",
            "steam_not_found": "Could not find the game on Steam.",
            "include_games": "Include games",
            "only_installed": "Installed only",
        },
    }

    def get_system_language() -> str:
        sys_lang = locale.getdefaultlocale()[0] or "en"
        return "es" if sys_lang.lower().startswith("es") else "en"

    def get_effective_language() -> str:
        return lang_var.get() if lang_var.get() != "system" else get_system_language()

    def tr(key: str) -> str:
        return LANG_TEXT[get_effective_language()][key]

    def login_steam_id() -> str | None:
        result = {"id": None}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                params = parse_qs(urlparse(self.path).query)
                claimed = params.get("openid.claimed_id", [None])[0]
                if claimed:
                    result["id"] = claimed.rsplit("/", 1)[-1]
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"Login successful. You may close this window.")
                else:
                    self.send_response(400)
                    self.end_headers()
                threading.Thread(target=httpd.shutdown).start()

            def log_message(self, format, *args):
                pass

        httpd = HTTPServer(("localhost", 5000), Handler)
        thread = threading.Thread(target=httpd.serve_forever)
        thread.start()
        params = {
            "openid.ns": "http://specs.openid.net/auth/2.0",
            "openid.mode": "checkid_setup",
            "openid.return_to": "http://localhost:5000/",
            "openid.realm": "http://localhost:5000/",
            "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select",
        }
        webbrowser.open("https://steamcommunity.com/openid/login?" + urlencode(params))
        thread.join()
        httpd.server_close()
        return result["id"]

    def import_steam_games() -> None:
        if not messagebox.askyesno("Steam", tr("steam_import_confirm")):
            return
        steam_id = login_steam_id()
        if not steam_id:
            return
        try:
            url = f"https://steamcommunity.com/profiles/{steam_id}/games?tab=all&xml=1"
            data = requests.get(url, timeout=10).content
            root_xml = ET.fromstring(data)
            games = [
                g.findtext("name")
                for g in root_xml.findall("./games/game")
                if g.findtext("name")
            ]
            games = list(dict.fromkeys(games))  # eliminate duplicates while preserving order
            if not games:
                raise ValueError
            hobby_id = use_cases.create_hobby(tr("steam_hobby_name"))
            all_existing = {
                s[2]
                for hid, _ in use_cases.get_all_hobbies()
                for s in use_cases.get_subitems_for_hobby(hid)
            }
            new_games = [g for g in games if g not in all_existing]
            for name in new_games:
                use_cases.add_subitem_to_hobby(hobby_id, name)
            refresh_listbox()
            if refresh_probabilities:
                refresh_probabilities()
            messagebox.showinfo("Steam", tr("steam_import_success").format(count=len(new_games)))
        except Exception:
            messagebox.showerror(tr("error"), tr("steam_import_error"))

    @lru_cache(maxsize=None)
    def get_steam_appid(game_name: str) -> int | None:
        try:
            resp = requests.get(
                "https://steamcommunity.com/actions/SearchApps/" + quote(game_name),
                timeout=5,
            )
            data = resp.json()
            return int(data[0]["appid"]) if data else None
        except Exception:
            return None

    @lru_cache(maxsize=None)
    def is_steam_game_installed(appid: int) -> bool:
        steam_paths = []
        if os.name == "nt":
            steam_paths.append(
                Path(os.environ.get("PROGRAMFILES(X86)", r"C:\\Program Files (x86)"))
                / "Steam/steamapps"
            )
        else:
            steam_paths.extend(
                [
                    Path.home() / ".steam/steam/steamapps",
                    Path.home() / ".local/share/Steam/steamapps",
                    Path.home() / "Library/Application Support/Steam/steamapps",
                ]
            )
        for path in steam_paths:
            if (path / f"appmanifest_{appid}.acf").exists():
                return True
        return False

    def show_game_popup(game_name: str) -> None:
        appid = get_steam_appid(game_name)
        if not appid:
            messagebox.showerror("Steam", tr("steam_not_found"))
            return
        installed = is_steam_game_installed(appid)
        dlg = tk.Toplevel(root)
        apply_style(dlg)
        dlg.title("Steam")
        dlg.transient(root)
        dlg.grab_set()
        WindowUtils.center_window(dlg, 300, 130)
        ttk.Label(
            dlg,
            text=tr("steam_action_prompt").format(name=game_name),
            justify="center",
            anchor="center",
        ).pack(padx=20, pady=15)

        def act() -> None:
            url = (
                f"steam://rungameid/{appid}"
                if installed
                else f"steam://install/{appid}"
            )
            webbrowser.open(url)
            dlg.destroy()

        btn = ttk.Button(
            dlg,
            text=tr("steam_play") if installed else tr("steam_install"),
            command=act,
            width=20,
        )
        btn.pack(pady=(0, 15))
        add_button_hover(btn)
    activity_lists = {}

    def build_activity_caches() -> None:
        """Cache weighted activity lists for quick toggle switches."""

        def filter_no_games(item):
            _, label, is_sub, _ = item
            return not (is_sub and label.startswith(tr("steam_hobby_name") + " + "))

        def filter_installed(item):
            _, label, is_sub, _ = item
            if not (is_sub and label.startswith(tr("steam_hobby_name") + " + ")):
                return True
            game_name = label.split(" + ", 1)[1]
            appid = get_steam_appid(game_name)
            return appid is not None and is_steam_game_installed(appid)

        activity_lists["all"] = use_cases.build_weighted_items()
        activity_lists["no_games"] = use_cases.build_weighted_items(filter_no_games)
        activity_lists["installed"] = use_cases.build_weighted_items(filter_installed)

    build_activity_caches()

    def current_items_weights():
        if not include_games_var.get():
            return activity_lists["no_games"]
        if installed_only_var.get():
            return activity_lists["installed"]
        return activity_lists["all"]

    canvas = None  # se asigna más tarde
    separator = None  # línea divisoria asignada después
    animation_canvas = None  # zona de animación para las sugerencias
    final_canvas = None  # capa final a pantalla completa
    button_container = None  # contenedor de botones inferior
    overlay_buttons = []  # referencias a botones del overlay
    final_timeout_id = None
    games_check = None  # toggle de incluir juegos
    installed_check = None  # toggle de solo instalados

    # --- Notebook principal ---
    notebook = ttk.Notebook(root)
    notebook.pack(fill="both", expand=True)

    # --- Menús de tema e idioma ---

    def change_theme_to(value: str) -> None:
        apply_style(root, value)
        if canvas is not None:
            canvas.configure(bg=get_color("surface"))
        if animation_canvas is not None:
            animation_canvas.configure(bg=get_color("surface"))
        if final_canvas is not None:
            final_canvas.configure(bg=get_color("surface"))
            final_canvas.itemconfigure("final_text", fill=get_color("text"))
        if refresh_probabilities:
            refresh_probabilities()
        save_settings()

    menubar = tk.Menu(root)

    def change_language(code: str) -> None:
        lang_var.set(code)
        update_texts()
        save_settings()

    def rebuild_menus() -> None:
        menubar.delete(0, "end")
        theme_menu = tk.Menu(menubar, tearoff=0)
        for key in ("system", "light", "dark"):
            theme_menu.add_radiobutton(
                label=tr(f"theme_{key}"),
                variable=theme_var,
                value=key,
                command=lambda k=key: change_theme_to(k),
            )
        menubar.add_cascade(label=tr("menu_theme"), menu=theme_menu)

        language_menu = tk.Menu(menubar, tearoff=0)
        for code, key in (("system", "lang_system"), ("es", "lang_spanish"), ("en", "lang_english")):
            language_menu.add_radiobutton(
                label=tr(key), value=code, variable=lang_var,
                command=lambda c=code: change_language(c)
            )
        menubar.add_cascade(label=tr("menu_language"), menu=language_menu)
        menubar.add_command(label="Steam", command=import_steam_games)
        root.config(menu=menubar)

    def update_texts() -> None:
        notebook.tab(0, text=tr("tab_today"))
        notebook.tab(1, text=tr("tab_config"))
        suggestion_label.config(text=tr("prompt"))
        suggest_btn.config(text=tr("suggest_button"))
        add_hobby_btn.config(text=tr("add_hobby"))
        prob_table.heading("activity", text=tr("col_activity"))
        prob_table.heading("percent", text=tr("col_percent"))
        rebuild_menus()
        if games_check is not None:
            games_check.config(text=tr("include_games"))
        if installed_check is not None:
            installed_check.config(text=tr("only_installed"))
        if final_canvas is not None and overlay_buttons:
            final_canvas.itemconfigure(
                "final_text", text=tr("what_about").format(current_activity["name"])
            )
            for btn, key in overlay_buttons:
                btn.config(text=tr(key))

    rebuild_menus()
    change_theme_to(theme_var.get())

    # --- Pestaña: ¿Qué hago hoy? ---
    frame_suggest = ttk.Frame(notebook, style="Surface.TFrame")
    notebook.add(frame_suggest, text=tr("tab_today"))

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
    prob_table.heading("activity", text=tr("col_activity"), anchor="w")
    prob_table.heading("percent", text=tr("col_percent"), anchor="center")
    prob_table.column("activity", width=480, anchor="w")
    prob_table.column("percent", width=180, anchor="center")

    v_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=prob_table.yview)
    prob_table.configure(yscrollcommand=v_scroll.set)

    prob_table.grid(row=0, column=0, sticky="nsew")
    v_scroll.grid(row=0, column=1, sticky="ns")

    def refresh_probabilities():
        for row in prob_table.get_children():
            prob_table.delete(row)
        prob_table.tag_configure(
            "even", background=get_color("surface"), foreground=get_color("text")
        )
        prob_table.tag_configure(
            "odd", background=get_color("light"), foreground=get_color("text")
        )
        items, weights = current_items_weights()
        if not items:
            return
        total_weight = sum(weights)
        for i, ((_, name, _), weight) in enumerate(zip(items, weights)):
            tag = "even" if i % 2 == 0 else "odd"
            prob = weight / total_weight
            prob_table.insert("", "end", values=(name, f"{prob*100:.1f}%"), tags=(tag,))

    refresh_probabilities()

    def on_toggle_update():
        nonlocal installed_check
        if not include_games_var.get():
            installed_only_var.set(False)
            if installed_check is not None:
                installed_check.state(["disabled"])
        else:
            if installed_check is not None:
                installed_check.state(["!disabled"])
        refresh_probabilities()

    suggestion_label = ttk.Label(
        content_frame,
        text=tr("prompt"),
        font=("Segoe UI", 28, "bold"),
        wraplength=500,
        justify="center",
        style="Surface.TLabel",
    )
    suggestion_label.pack(pady=20, expand=True)

    animation_canvas = tk.Canvas(
        content_frame,
        width=1620,
        height=220,
        bg=get_color("surface"),
        highlightthickness=0,
    )

    current_activity = {"id": None, "name": None, "is_subitem": False}

    def revert_to_idle() -> None:
        nonlocal final_canvas, final_timeout_id
        if final_canvas is not None:
            final_canvas.destroy()
            final_canvas = None
            if separator is not None:
                separator.grid()
            if table_frame is not None:
                table_frame.grid()
            button_container.pack(side="bottom", fill="x", pady=20)
        overlay_buttons.clear()
        suggest_btn.state(["!disabled"])
        suggestion_label.config(text=tr("prompt"))
        suggestion_label.pack(pady=20, expand=True)
        final_timeout_id = None

    def show_final_activity(text: str) -> None:
        nonlocal final_canvas, final_timeout_id
        if final_timeout_id is not None:
            root.after_cancel(final_timeout_id)
            final_timeout_id = None
        if final_canvas is not None:
            final_canvas.destroy()

        final_canvas = tk.Canvas(frame_suggest, bg=get_color("surface"), highlightthickness=0)
        final_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        final_canvas.update_idletasks()

        if separator is not None:
            separator.grid_remove()
        if table_frame is not None:
            table_frame.grid_remove()
        # Oculta la botonera base, NO la metas en el canvas
        button_container.pack_forget()

        cx = final_canvas.winfo_width() / 2
        cy = final_canvas.winfo_height() / 2
        max_width = final_canvas.winfo_width() * 0.9

        text_item = final_canvas.create_text(
            cx,
            cy,
            text=text,
            width=max_width,
            fill=get_color("text"),
            font=("Segoe UI", 28, "bold"),
            tags=("final_text",),
            justify="center",
            anchor="center",
        )

        # >>> NUEVO: crear botonera específica de overlay <<<
        overlay_buttons = make_overlay_buttons(final_canvas)
        button_window = final_canvas.create_window(
            cx, final_canvas.winfo_height() - 20, window=overlay_buttons, anchor="s"
        )

        def on_resize(event=None):
            nonlocal max_width
            max_width = final_canvas.winfo_width() * 0.9
            final_canvas.itemconfigure(text_item, width=max_width)
            final_canvas.coords(
                text_item,
                final_canvas.winfo_width() / 2,
                final_canvas.winfo_height() / 2,
            )
            final_canvas.coords(
                button_window,
                final_canvas.winfo_width() / 2,
                final_canvas.winfo_height() - 20,
            )

        final_canvas.bind("<Configure>", on_resize)

        def launch_confetti():
            width = final_canvas.winfo_width()
            height = final_canvas.winfo_height()
            colors = ["#FF5E5E","#FFD700","#5EFF5E","#5E5EFF","#FF5EFF","#FFA500"]

            def create_piece():
                x = random.randint(0, width)
                size = random.randint(5, 12)
                color = random.choice(colors)
                piece = final_canvas.create_rectangle(x, -size, x+size, 0, fill=color, outline="")
                dy = random.uniform(3, 6)
                def fall():
                    final_canvas.move(piece, 0, dy)
                    if final_canvas.coords(piece)[3] < height:
                        final_canvas.after(30, fall)
                    else:
                        final_canvas.delete(piece)
                fall()

            for i in range(80):
                final_canvas.after(i*20, create_piece)

        launch_confetti()
        final_timeout_id = root.after(8000, revert_to_idle)

    def suggest():
        nonlocal final_canvas, final_timeout_id
        for btn, _ in overlay_buttons:
            btn.state(["disabled"])
        suggest_btn.state(["disabled"])
        if final_timeout_id is not None:
            root.after_cancel(final_timeout_id)
            final_timeout_id = None
        if final_canvas is not None:
            final_canvas.destroy()
            final_canvas = None
            if separator is not None:
                separator.grid()
            if table_frame is not None:
                table_frame.grid()
            button_container.pack(side="bottom", fill="x", pady=20)
        items, weights = current_items_weights()
        result = random.choices(items, weights=weights, k=1)[0] if items else None
        if not result:
            suggestion_label.config(
                text=tr("no_hobbies")
            )
            suggestion_label.pack(pady=20, expand=True)
            return

        final_id, final_text, is_sub = result
        current_activity["id"] = final_id
        current_activity["name"] = final_text
        current_activity["is_subitem"] = is_sub

        options = []
        for _ in range(20):
            if items:
                alt = random.choices(items, weights=weights, k=1)[0]
                options.append(alt[1])
        options += [final_text, ""]

        animation_canvas.delete("all")
        box_w, box_h = 540, 180
        #box_colors = ["#FFEBEE", "#E3F2FD", "#E8F5E9", "#FFF3E0", "#F3E5F5"]
        for i, text in enumerate(options):
            x = i * box_w
            #color = random.choice(box_colors)
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
                width=box_w - 20,
                fill=get_color("text"),
                font=("Segoe UI", 32, "bold"),
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
        animation_canvas.pack(pady=20, before=button_container)

        total_shift = (len(options) - 3) * box_w

        def roll(step=0, speed=10):
            if step < total_shift:
                animation_canvas.move("item", -speed, 0)
                step += speed
                if step < total_shift * 0.6:
                    speed = min(speed + 2, 80)
                elif total_shift - step < box_w * 2:
                    speed = max(speed - 3, 5)
                root.after(20, lambda: roll(step, speed))
            else:
                animation_canvas.move("item", -(total_shift - step), 0)
                animation_canvas.after(200, finish)

        def finish():
            animation_canvas.pack_forget()
            show_final_activity(tr("what_about").format(final_text))
            # habilitar acciones en la capa final
            for btn, key in overlay_buttons:
                if key in ("like_overlay", "another_button"):
                    btn.state(["!disabled"])
        
        roll()

    def accept():
        nonlocal final_canvas, final_timeout_id
        if current_activity["id"]:
            is_game = (
                current_activity["is_subitem"]
                and current_activity["name"]
                and current_activity["name"].startswith(tr("steam_hobby_name") + " + ")
            )
            game_name = (
                current_activity["name"].split(" + ", 1)[1]
                if is_game
                else ""
            )
            use_cases.mark_activity_as_done(
                current_activity["id"], current_activity["is_subitem"]
            )
            build_activity_caches()
            if is_game:
                show_game_popup(game_name)
            current_activity["id"] = None
            current_activity["name"] = None
            current_activity["is_subitem"] = False
            suggestion_label.config(text=tr("prompt"))
            suggestion_label.pack(pady=20, expand=True)
            if final_timeout_id is not None:
                root.after_cancel(final_timeout_id)
                final_timeout_id = None
            if final_canvas is not None:
                final_canvas.destroy()
                final_canvas = None
                if separator is not None:
                    separator.grid()
                if table_frame is not None:
                    table_frame.grid()
                button_container.pack(side="bottom", fill="x", pady=20)
            overlay_buttons.clear()
            suggest_btn.state(["!disabled"])
            refresh_probabilities()

    def make_overlay_buttons(parent):
        """Botonera específica para la capa final (parent debe ser final_canvas)."""
        nonlocal overlay_buttons
        overlay_buttons = []
        overlay = ttk.Frame(parent, style="Surface.TFrame")
        btn1 = ttk.Button(
            overlay, text=tr("another_button"), command=suggest, style="Big.TButton", width=20
        )
        btn1.pack(side="left", padx=8, pady=10)
        add_button_hover(btn1)
        btn1.state(["disabled"])  # deshabilitado mientras dura la animación
        overlay_buttons.append((btn1, "another_button"))
        btn2 = ttk.Button(
            overlay, text=tr("like_overlay"), command=accept, style="Big.TButton", width=20
        )
        btn2.pack(side="left", padx=8, pady=10)
        add_button_hover(btn2)
        overlay_buttons.append((btn2, "like_overlay"))
        return overlay

    button_container = ttk.Frame(content_frame, style="Surface.TFrame")
    button_container.pack(side="bottom", fill="x", pady=20)

    toggle_frame = ttk.Frame(button_container, style="Surface.TFrame")
    toggle_frame.pack(pady=(0, 10))

    games_check = ttk.Checkbutton(
        toggle_frame,
        text=tr("include_games"),
        variable=include_games_var,
        command=on_toggle_update,
    )
    games_check.pack(side="left", padx=5)

    installed_check = ttk.Checkbutton(
        toggle_frame,
        text=tr("only_installed"),
        variable=installed_only_var,
        command=on_toggle_update,
    )
    installed_check.pack(side="left", padx=5)

    on_toggle_update()

    suggest_btn = ttk.Button(
        button_container,
        text=tr("suggest_button"),
        command=suggest,
        style="Big.TButton",
        width=20,
    )
    suggest_btn.pack(pady=10)
    add_button_hover(suggest_btn)

    def on_tab_change(event):
        if notebook.index("current") == 0:
            refresh_probabilities()

    notebook.bind("<<NotebookTabChanged>>", on_tab_change)

    # --- Pestaña: Configurar hobbies ---
    frame_config = ttk.Frame(notebook, style="Surface.TFrame")
    notebook.add(frame_config, text=tr("tab_config"))

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
    add_hobby_btn = ttk.Button(
        sticky_bottom, text=tr("add_hobby"), command=lambda: open_add_hobby_window()
    )
    add_hobby_btn.pack()

    update_texts()

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
            tr("delete"), tr("delete_hobby_confirm").format(name=hobby_name)
        ):
            use_cases.delete_hobby(hobby_id)
            refresh_listbox()
            messagebox.showinfo(tr("deleted"), tr("hobby_deleted").format(name=hobby_name))

    def open_edit_hobby_window(hobby_id, hobby_name):
        edit_window = tk.Toplevel()
        apply_style(edit_window)
        edit_window.title(tr("edit_hobby_title").format(name=hobby_name))
        WindowUtils.center_window(edit_window, 600, 600)
        edit_window.minsize(600, 600)

        ttk.Label(edit_window, text=tr("subitems")).pack(pady=5)
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
                        title=tr("edit_subitem_title"),
                        prompt=tr("new_name_prompt").format(name=current_name),
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
            if messagebox.askyesno(
                tr("delete"), tr("delete_subitem_confirm").format(name=name)
            ):
                use_cases.delete_subitem(item_id)
                refresh_items()

        def add_subitem():
            new_item = SimpleEntryDialog.ask(
                parent=edit_window,
                title=tr("new_subitem_title"),
                prompt=tr("new_subitem_prompt"),
            )
            if new_item:
                use_cases.add_subitem_to_hobby(hobby_id, new_item.strip())
                refresh_items()

        ttk.Button(
            edit_window, text=tr("add_subitem_btn"), command=add_subitem
        ).pack(pady=10)
        refresh_items()

    def open_add_hobby_window():
        def save_hobby():
            name = hobby_entry.get().strip()
            if not name:
                messagebox.showerror(tr("error"), tr("need_title"))
                return
            hobby_id = use_cases.create_hobby(name)
            sub = SimpleEntryDialog.ask(
                parent=add_window, title=tr("subitem_title"), prompt=tr("subitem_prompt"),
            )
            while sub:
                use_cases.add_subitem_to_hobby(hobby_id, sub.strip())
                sub = SimpleEntryDialog.ask(
                    parent=add_window,
                    title=tr("another_title"),
                    prompt=tr("another_prompt"),
                )
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

    refresh_listbox()
    root.mainloop()
