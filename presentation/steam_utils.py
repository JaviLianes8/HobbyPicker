import os
import re
import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlencode, urlparse, parse_qs, quote
import xml.etree.ElementTree as ET
from functools import lru_cache
import requests


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


def fetch_steam_games(steam_id: str) -> list[str]:
    url = f"https://steamcommunity.com/profiles/{steam_id}/games?tab=all&xml=1"
    data = requests.get(url, timeout=10).content
    root_xml = ET.fromstring(data)
    games = [
        g.findtext("name")
        for g in root_xml.findall("./games/game")
        if g.findtext("name")
    ]
    return list(dict.fromkeys(games))


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


@lru_cache(maxsize=1)
def discover_steam_libraries() -> list[Path]:
    paths: list[Path] = []
    candidate_roots: list[Path] = []
    if os.name == "nt":
        pf_x86 = os.environ.get("PROGRAMFILES(X86)")
        pf = os.environ.get("PROGRAMFILES")
        if pf_x86:
            candidate_roots.append(Path(pf_x86) / "Steam")
        if pf:
            candidate_roots.append(Path(pf) / "Steam")
        for letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            base = Path(f"{letter}:/")
            candidate_roots.extend(
                [
                    base / "Steam",
                    base / "SteamLibrary",
                    base / "Program Files/Steam",
                    base / "Program Files (x86)/Steam",
                ]
            )
    else:
        candidate_roots.extend(
            [
                Path.home() / ".steam/steam",
                Path.home() / ".local/share/Steam",
                Path.home() / "Library/Application Support/Steam",
            ]
        )
    for root in candidate_roots:
        steamapps = root / "steamapps"
        if steamapps.exists():
            paths.append(steamapps)
            vdf = steamapps / "libraryfolders.vdf"
            if vdf.exists():
                try:
                    text = vdf.read_text(encoding="utf-8", errors="ignore")
                    for folder in re.findall(r'"path"\s*"([^"]+)"', text):
                        lib_path = Path(folder).expanduser()
                        candidate = lib_path / "steamapps"
                        if candidate.exists():
                            paths.append(candidate)
                except Exception:
                    pass
    unique: list[Path] = []
    for p in paths:
        resolved = p.resolve()
        if resolved not in unique:
            unique.append(resolved)
    return unique


def _normalize_game_name(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", name.lower())


@lru_cache(maxsize=1)
def load_installed_games() -> dict[str, int]:
    games: dict[str, int] = {}
    for path in discover_steam_libraries():
        for manifest in path.glob("appmanifest_*.acf"):
            try:
                text = manifest.read_text(encoding="utf-8", errors="ignore")
                appid_match = re.search(r'"appid"\s*"(\d+)"', text)
                name_match = re.search(r'"name"\s*"([^\"]+)"', text)
                if appid_match and name_match:
                    games[_normalize_game_name(name_match.group(1))] = int(
                        appid_match.group(1)
                    )
            except Exception:
                pass
    return games


def get_local_appid(game_name: str) -> int | None:
    return load_installed_games().get(_normalize_game_name(game_name))
