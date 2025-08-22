"""Utility functions for interacting with Steam."""
from __future__ import annotations
import os, re, threading, webbrowser
from functools import lru_cache
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs, quote
import xml.etree.ElementTree as ET
import requests
import tkinter as tk
from tkinter import messagebox, ttk
from domain import use_cases
from presentation.widgets.styles import apply_style, add_button_hover
from presentation.utils.window_utils import WindowUtils
from .translations import tr, STEAM_HOBBY_NAMES

def is_steam_game_label(label: str) -> bool:
    return any(label.startswith(name + " + ") for name in STEAM_HOBBY_NAMES)

def login_steam_id() -> str | None:
    result={"id":None}
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            params=parse_qs(urlparse(self.path).query)
            claimed=params.get("openid.claimed_id",[None])[0]
            if claimed:
                result["id"]=claimed.rsplit("/",1)[-1]
                self.send_response(200);self.end_headers()
                self.wfile.write(b"Login successful. You may close this window.")
            else:
                self.send_response(400);self.end_headers()
            threading.Thread(target=httpd.shutdown).start()
        def log_message(self,format,*args):pass
    httpd=HTTPServer(("localhost",5000),Handler)
    thread=threading.Thread(target=httpd.serve_forever);thread.start()
    params={"openid.ns":"http://specs.openid.net/auth/2.0","openid.mode":"checkid_setup",
            "openid.return_to":"http://localhost:5000/","openid.realm":"http://localhost:5000/",
            "openid.identity":"http://specs.openid.net/auth/2.0/identifier_select",
            "openid.claimed_id":"http://specs.openid.net/auth/2.0/identifier_select"}
    webbrowser.open("https://steamcommunity.com/openid/login?"+urlencode(params))
    thread.join();httpd.server_close();return result["id"]

def import_steam_games(build_activity_caches, refresh_listbox)->None:
    if not messagebox.askyesno("Steam",tr("steam_import_confirm")):return
    steam_id=login_steam_id()
    if not steam_id:return
    try:
        url=f"https://steamcommunity.com/profiles/{steam_id}/games?tab=all&xml=1"
        data=requests.get(url,timeout=10).content
        root_xml=ET.fromstring(data)
        games=[g.findtext("name") for g in root_xml.findall("./games/game") if g.findtext("name")]
        games=list(dict.fromkeys(games))
        if not games:raise ValueError
        hobby_id=use_cases.create_hobby(tr("steam_hobby_name"))
        all_existing={s[2] for hid,_ in use_cases.get_all_hobbies() for s in use_cases.get_subitems_for_hobby(hid)}
        new_games=[g for g in games if g not in all_existing]
        for name in new_games:use_cases.add_subitem_to_hobby(hobby_id,name)
        build_activity_caches();refresh_listbox()
        messagebox.showinfo("Steam",tr("steam_import_success").format(count=len(new_games)))
    except Exception:
        messagebox.showerror(tr("error"),tr("steam_import_error"))

@lru_cache(maxsize=None)
def get_steam_appid(game_name:str)->int|None:
    try:
        resp=requests.get("https://steamcommunity.com/actions/SearchApps/"+quote(game_name),timeout=5)
        data=resp.json();return int(data[0]["appid"]) if data else None
    except Exception:return None

@lru_cache(maxsize=1)
def discover_steam_libraries()->list[Path]:
    paths=[];candidate=[]
    if os.name=="nt":
        pf_x86=os.environ.get("PROGRAMFILES(X86)");pf=os.environ.get("PROGRAMFILES")
        if pf_x86:candidate.append(Path(pf_x86)/"Steam")
        if pf:candidate.append(Path(pf)/"Steam")
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            base=Path(f"{letter}:/")
            candidate+=[base/"Steam",base/"SteamLibrary",base/"Program Files/Steam",base/"Program Files (x86)/Steam"]
    else:
        candidate+=[Path.home()/".steam/steam",Path.home()/".local/share/Steam",Path.home()/"Library/Application Support/Steam"]
    for root in candidate:
        steamapps=root/"steamapps"
        if steamapps.exists():
            paths.append(steamapps)
            vdf=steamapps/"libraryfolders.vdf"
            if vdf.exists():
                try:
                    text=vdf.read_text(encoding="utf-8",errors="ignore")
                    for folder in re.findall(r'"path"\s*"([^"]+)"',text):
                        lib_path=Path(folder).expanduser();candidate_path=lib_path/"steamapps"
                        if candidate_path.exists():paths.append(candidate_path)
                except Exception:pass
    unique=[];[unique.append(p.resolve()) for p in paths if p.resolve() not in unique]
    return unique

def _normalize_game_name(name:str)->str:
    return re.sub(r"[^a-z0-9]+","",name.lower())

@lru_cache(maxsize=1)
def load_installed_games()->dict[str,int]:
    games={}
    for path in discover_steam_libraries():
        for manifest in path.glob("appmanifest_*.acf"):
            try:
                text=manifest.read_text(encoding="utf-8",errors="ignore")
                appid_match=re.search(r'"appid"\s*"(\d+)"',text)
                name_match=re.search(r'"name"\s*"([^\"]+)"',text)
                if appid_match and name_match:
                    games[_normalize_game_name(name_match.group(1))]=int(appid_match.group(1))
            except Exception:pass
    return games

def get_local_appid(game_name:str)->int|None:
    return load_installed_games().get(_normalize_game_name(game_name))

def show_game_popup(root:tk.Tk,game_name:str)->None:
    load_installed_games.cache_clear()
    appid=get_local_appid(game_name);installed=appid is not None
    if not installed:appid=get_steam_appid(game_name)
    if not appid:messagebox.showerror("Steam",tr("steam_not_found"));return
    dlg=tk.Toplevel(root);apply_style(dlg);dlg.title("Steam");dlg.transient(root);dlg.grab_set()
    WindowUtils.center_window(dlg,600,130)
    ttk.Label(dlg,text=tr("steam_action_prompt").format(name=game_name),justify="center",anchor="center",wraplength=560).pack(padx=20,pady=15)
    def act()->None:
        local_id=get_local_appid(game_name)
        if local_id:webbrowser.open(f"steam://rungameid/{local_id}")
        else:webbrowser.open(f"steam://rungameid/{appid}");webbrowser.open(f"steam://install/{appid}")
        dlg.destroy()
    btn=ttk.Button(dlg,text=tr("steam_play") if installed else tr("steam_install"),command=act,width=20)
    btn.pack(pady=(0,15));add_button_hover(btn)
