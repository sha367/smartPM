# Точка входа для Streamlit Cloud
import sys
import os

# Добавляем текущую директорию в путь
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Импортируем и запускаем новое приложение
from business_case_app import main

if __name__ == "__main__":
    main() 