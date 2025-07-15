import subprocess
import sys
import os

def check_and_launch():
    # Verificar si el repositorio está actualizado
    repo_path = os.path.dirname(__file__)
    os.chdir(repo_path)

    subprocess.run(["git", "fetch", "origin"], stdout=subprocess.DEVNULL)

    local = subprocess.check_output(["git", "rev-parse", "HEAD"]).strip()
    remote = subprocess.check_output(["git", "rev-parse", "origin/main"]).strip()

    if local != remote:
        print("🔄 Actualizando desde main...")
        subprocess.run(["git", "pull", "origin", "main"])
        print("✅ Actualizado. Reiniciando...")
        python = sys.executable
        script = os.path.join(repo_path, "main.pyw")
        os.execv(python, [python, script])
    else:
        print("✅ Ya estás en la última versión.")
        from presentation.app import start_app
        start_app()