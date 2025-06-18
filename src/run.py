import subprocess
import sys
import os
import venv
from pathlib import Path

def create_venv(venv_path):
    """Crea un entorno virtual si no existe"""
    if not os.path.exists(venv_path):
        print("Creando entorno virtual...")
        venv.create(venv_path, with_pip=True)
        return True
    return False

def get_python_path(venv_path):
    """Obtiene la ruta al ejecutable de Python en el entorno virtual"""
    if sys.platform == "win32":
        python_path = os.path.join(venv_path, "Scripts", "python.exe")
    else:
        python_path = os.path.join(venv_path, "bin", "python")
    return python_path

def install_requirements(python_path, requirements_path):
    """Instala las dependencias desde requirements.txt"""
    print("Instalando dependencias...")
    subprocess.check_call([python_path, "-m", "pip", "install", "-r", requirements_path])

def run_app(python_path):
    """Ejecuta la aplicación Flask en modo producción"""
    import src
    app = src.create_app()

    # Ejecutar siempre en modo producción
    app.run(debug=True)

if __name__ == "__main__":
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src_path = os.path.dirname(os.path.abspath(__file__))

    venv_path = os.path.join(base_path, ".venv")
    requirements_path = os.path.join(src_path, "requirements.txt")

    # Asegurar que Python pueda encontrar src como paquete
    sys.path.insert(0, base_path)

    # Establecer FLASK_ENV explícitamente como producción
    os.environ["FLASK_ENV"] = "production"

    try:
        if create_venv(venv_path):
            print("Entorno virtual creado exitosamente.")

        python_path = get_python_path(venv_path)

        if not os.path.exists(os.path.join(os.path.dirname(python_path), "pip.exe" if sys.platform == "win32" else "pip")):
            install_requirements(python_path, requirements_path)
            print("Dependencias instaladas correctamente.")

        print("Iniciando la aplicación en modo producción...")
        run_app(python_path)

    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
