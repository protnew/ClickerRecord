import os
import sys
import subprocess
import shutil
import time

def check_exe_exists():
    """Проверяет наличие clicker.exe в папке dist"""
    exe_path = os.path.join("dist", "clicker.exe")
    if not os.path.exists(exe_path):
        print("Ошибка: файл clicker.exe не найден в папке dist")
        print("Сначала нужно собрать EXE-файл с помощью build.py")
        return False
    return True

def check_nsis_installed():
    """Проверяет наличие установленного NSIS"""
    # Типичные пути установки NSIS
    nsis_paths = [
        r"C:\Program Files\NSIS\makensis.exe",
        r"C:\Program Files (x86)\NSIS\makensis.exe"
    ]
    
    for path in nsis_paths:
        if os.path.exists(path):
            return path
    
    print("ПРЕДУПРЕЖДЕНИЕ: NSIS не найден по стандартным путям установки.")
    print("Если NSIS установлен в нестандартной папке, инсталлятор не будет создан.")
    print("Вы можете скачать NSIS с сайта: https://nsis.sourceforge.io/Download")
    
    # Пытаемся найти NSIS через переменную PATH
    try:
        result = subprocess.run(["where", "makensis"], capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")[0]
    except:
        pass
    
    return None

def check_required_files():
    """Проверяет наличие всех необходимых файлов для инсталлятора"""
    required_files = [
        "icon.ico",
        "license.txt",
        "installer_welcome.bmp",
        "installer_header.bmp",
        "installer.nsi"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"Ошибка: не найдены следующие файлы: {', '.join(missing_files)}")
        return False
    
    return True

def build_installer(nsis_path):
    """Сборка инсталлятора с помощью NSIS"""
    try:
        print("Начало сборки инсталлятора...")
        
        # Запуск процесса сборки
        process = subprocess.Popen(
            [nsis_path, "installer.nsi"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Вывод прогресса сборки
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        
        # Проверка результата сборки
        if process.returncode == 0:
            installer_path = "clicker_setup.exe"
            if os.path.exists(installer_path):
                print(f"\nСборка инсталлятора успешно завершена!")
                print(f"Инсталлятор находится здесь: {os.path.abspath(installer_path)}")
                return True
            else:
                print("Ошибка: инсталлятор не найден после сборки")
                return False
        else:
            print("Ошибка при сборке инсталлятора")
            return False
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        return False

def main():
    # Проверяем наличие EXE-файла
    if not check_exe_exists():
        return
    
    # Проверяем наличие NSIS
    nsis_path = check_nsis_installed()
    if not nsis_path:
        print("Инсталлятор не может быть создан: NSIS не найден")
        return
    
    # Проверяем наличие всех необходимых файлов
    if not check_required_files():
        return
    
    # Сборка инсталлятора
    build_installer(nsis_path)

if __name__ == "__main__":
    main() 