import subprocess, sys, os

def _sh(*args, check=True, text=True):
    return subprocess.run(args, check=check, text=text, capture_output=True).stdout.strip()

def check_and_launch():
    # Asegura que estamos en la raíz del repo (no en una subcarpeta)
    repo_root = _sh("git", "rev-parse", "--show-toplevel")
    os.chdir(repo_root)

    # Rama actual (si estás en detached HEAD, esto fallará → tratamos como "no main")
    try:
        branch = _sh("git", "symbolic-ref", "--short", "HEAD")
    except subprocess.CalledProcessError:
        branch = "HEAD"  # detached

    # Upstream de la rama (puede no existir)
    try:
        upstream = _sh("git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    except subprocess.CalledProcessError:
        upstream = ""

    # Si NO es main o NO trackea origin/main → no hacemos pull
    if not (branch == "main" and upstream == "origin/main"):
        print(f"⚠️ Estás en '{branch}' (upstream: '{upstream or '—'}'), no se hace pull automático.")
        from presentation.app import start_app
        start_app()
        return

    # Evita sobrescribir cambios locales
    dirty_wc = subprocess.run(["git", "diff", "--quiet"]).returncode != 0
    dirty_index = subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode != 0
    if dirty_wc or dirty_index:
        print("⚠️ Tienes cambios locales. No hago pull para no pisarlos.")
        from presentation.app import start_app
        start_app()
        return

    subprocess.run(["git", "fetch", "origin"], stdout=subprocess.DEVNULL)

    local = _sh("git", "rev-parse", "HEAD")
    remote = _sh("git", "rev-parse", "origin/main")

    if local != remote:
        print("🔄 Actualizando desde origin/main…")
        subprocess.run(["git", "pull", "--ff-only", "origin", "main"], check=True)
        print("✅ Actualizado. Reiniciando…")
        python = sys.executable
        script = os.path.join(repo_root, "main.py")
        os.execv(python, [python, script])
    else:
        print("✅ Ya estás en la última versión.")
        from presentation.app import start_app
        start_app()

if __name__ == "__main__":
    check_and_launch()
