import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, date
import os
import json
import uuid

# Конфигурация страницы
st.set_page_config(
    page_title="Управление бизнес-кейсами",
    page_icon="💼",
    layout="wide"
)

# Путь к Excel файлам
EXCEL_FILES = [
    "/Users/Vasily_Lukin/Downloads/Бизнес_кейс_Михненко_Екатерина.xlsx",
    "/Users/Vasily_Lukin/Downloads/Бизнес_кейс_Зырянова.xlsx",
    "/Users/Vasily_Lukin/Downloads/Бизнес_кейс. Руслан Амерханов.xlsx"
]
PROJECTS_FILE = "/Users/Vasily_Lukin/projects_database.json"
CHANGELOG_FILE = "/Users/Vasily_Lukin/changelog.json"

# L-статусы с описаниями
L_STATUSES = {
    "L0": {"name": "Идея", "description": "Сбор всех идей, независимо от реализуемости или масштаба"},
    "L1": {"name": "Идентифицировано", "description": "Инициатива признана перспективной, проводится первичная оценка и уточнение"},
    "L2": {"name": "Планирование", "description": "Разработка подробного бизнес-кейса, утверждение инициативы"},
    "L3": {"name": "Исполнение", "description": "Реализация инициативы по утвержденному плану, выполнение ключевых мероприятий"},
    "L4": {"name": "Завершено", "description": "Все шаги по реализации завершены, идет проверка достижения целевых показателей"},
    "L5": {"name": "Реализовано", "description": "Фактическая ценность подтверждена в бизнес-результатах"}
}

# Инициализация состояния
if 'current_view' not in st.session_state:
    st.session_state.current_view = "projects_list"  # projects_list, project_detail, new_project, changelog

if 'selected_project' not in st.session_state:
    st.session_state.selected_project = None

if 'selected_section' not in st.session_state:
    st.session_state.selected_section = None

if 'projects_database' not in st.session_state:
    st.session_state.projects_database = {}

if 'changelog' not in st.session_state:
    st.session_state.changelog = []

def generate_sample_status_data():
    """Генерируем тестовые данные для статусов инициатив"""
    status_data = pd.DataFrame({
        "Инициатива": [
            "Увеличение конверсии сайта",
            "Внедрение CRM системы", 
            "Автоматизация отчетности",
            "Обучение менеджеров",
            "Оптимизация логистики",
            "Цифровизация процессов"
        ],
        "Статус": ["L3", "L2", "L4", "L1", "L3", "L5"],
        "Владелец": [
            "А. Петров",
            "М. Иванова", 
            "С. Сидоров",
            "Н. Козлова",
            "В. Попов",
            "Е. Морозова"
        ],
        "Прогресс (%)": [75, 45, 90, 20, 65, 100],
        "Плановый эффект (млн руб)": [35, 120, 15, 8, 45, 200],
        "Фактический эффект (млн руб)": [28, 0, 14, 0, 30, 195],
        "Дата начала": [
            "2024-01-15", "2024-03-01", "2023-11-01", 
            "2024-06-01", "2024-02-15", "2023-08-01"
        ],
        "Планируемое завершение": [
            "2024-12-31", "2025-01-31", "2024-08-31",
            "2024-12-31", "2025-03-31", "2024-06-30"
        ],
        "Ключевые вехи": [
            "Настройка аналитики, A/B тесты",
            "Выбор решения, интеграция",
            "Автоматические дашборды",
            "Программа обучения, сертификация", 
            "Новые маршруты, склады",
            "Полная автоматизация"
        ],
        "Риски": [
            "Низкий трафик в Q4",
            "Сложность интеграции",
            "Сопротивление пользователей",
            "Высокая текучесть кадров",
            "Рост стоимости топлива",
            "Поддержка системы"
        ],
        "Комментарии": [
            "Результаты превышают ожидания",
            "Требуется дополнительный бюджет",
            "Завершено досрочно",
            "Поиск внешнего провайдера",
            "Пилотный проект успешен",
            "Достигнут ROI 300%"
        ]
    })
    return status_data

@st.cache_data
def load_excel_data():
    """Загружаем все листы из Excel файлов"""
    all_data = {}
    
    # Используем только файл Михненко для всех проектов
    master_file = "/Users/Vasily_Lukin/Downloads/Бизнес_кейс_Михненко_Екатерина.xlsx"
    
    try:
        if os.path.exists(master_file):
            excel_data = pd.read_excel(master_file, sheet_name=None)
            filename = os.path.basename(master_file).replace('.xlsx', '')
            
            for sheet_name, df in excel_data.items():
                # Сохраняем под несколькими ключами для всех проектов:
                
                # 1. Полный ключ для совместимости
                unique_key = f"{filename}_{sheet_name}"
                all_data[unique_key] = df.copy()
                
                # 2. Простое название раздела для прямого доступа
                all_data[sheet_name] = df.copy()
                
                # 3. Ключи с префиксом каждого проекта
                for project_id in ["business_case_1", "business_case_2", "business_case_3"]:
                    project_section_key = f"{project_id}_{sheet_name}"
                    all_data[project_section_key] = df.copy()
            
            st.success(f"✅ Загружен мастер файл: {filename}")
            st.info(f"📊 Загружено разделов: {', '.join(excel_data.keys())}")
            
    except Exception as e:
        st.error(f"❌ Не удалось загрузить мастер файл {master_file}: {e}")
        
        # Создаем пустые данные как резерв
        default_sections = [
            "a. Детали инициативы",
            "b. Финансовое влияние", 
            "c. Поддерживающие расчеты",
            "d. Диаграмма Ганта",
            "e. Мониторинг эффекта",
            "f. Статус инициатив"
        ]
        
        for section in default_sections:
            empty_df = pd.DataFrame({
                "Параметр": ["Пример параметра"],
                "Значение": ["Пример значения"],
                "Комментарий": ["Пример комментария"]
            })
            all_data[section] = empty_df
            
            # Для всех проектов
            for project_id in ["business_case_1", "business_case_2", "business_case_3"]:
                all_data[f"{project_id}_{section}"] = empty_df.copy()
    
    # Добавляем тестовые данные для статусов инициатив если их нет
    status_section = "f. Статус инициатив"
    if status_section not in all_data or all_data[status_section].empty:
        sample_data = generate_sample_status_data()
        all_data[status_section] = sample_data
        
        for project_id in ["business_case_1", "business_case_2", "business_case_3"]:
            all_data[f"{project_id}_{status_section}"] = sample_data.copy()
    
    return all_data

def load_changelog():
    """Загружаем историю изменений"""
    try:
        if os.path.exists(CHANGELOG_FILE):
            with open(CHANGELOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Ошибка загрузки истории изменений: {e}")
    return []

def save_changelog(changelog):
    """Сохраняем историю изменений"""
    try:
        with open(CHANGELOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(changelog, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения истории изменений: {e}")
        return False

def add_changelog_entry(project_id, action, details, user="Текущий пользователь"):
    """Добавляем запись в историю изменений"""
    entry = {
        "id": str(uuid.uuid4()),
        "project_id": project_id,
        "timestamp": datetime.now().isoformat(),
        "user": user,
        "action": action,
        "details": details
    }
    
    if 'changelog' not in st.session_state:
        st.session_state.changelog = load_changelog()
    
    st.session_state.changelog.append(entry)
    save_changelog(st.session_state.changelog)

def load_projects_database():
    """Загружаем базу данных проектов"""
    try:
        if os.path.exists(PROJECTS_FILE):
            with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Ошибка загрузки базы проектов: {e}")
    
    # Возвращаем начальные проекты из Excel файлов
    today = datetime.now().strftime("%Y-%m-%d")
    
    projects = {
        "business_case_1": {
            "id": "business_case_1",
            "name": "Династия докторов - увеличение выручки",
            "description": "Проект по увеличению выручки через цифровизацию и оптимизацию коммерческих процессов. Целевой показатель: 35 млн руб в текущем году, 80-100 млн руб в перспективе.",
            "sections": {
                "a. Детали инициативы": "Основная информация об инициативе, цели и описание",
                "b. Финансовое влияние": "Финансовые показатели и прогнозы по годам",
                "c. Поддерживающие расчеты": "Расчеты конверсии и KPI",
                "d. Диаграмма Ганта": "Временной план выполнения задач",
                "e. Мониторинг эффекта": "Ежемесячное отслеживание результатов",
                "f. Статус инициатив": "Текущий статус реализации и прогресс"
            },
            "status": "L3",
            "owner": "Екатерина Михненко",
            "department": "Маркетинг и продажи",
            "start_date": "2024-01-15",
            "end_date": "2024-12-15",
            "last_updated": today,
            "created_date": "2024-01-01",
            "target_revenue": "35 млн руб (2024), 80-100 млн руб (проекция)",
            "key_metrics": "Конверсия 0.6→0.7, выручка +35М руб"
        }
    }
    
    # Добавляем проекты для других файлов если они существуют
    if os.path.exists("/Users/Vasily_Lukin/Downloads/Бизнес_кейс_Зырянова.xlsx"):
        projects["business_case_2"] = {
            "id": "business_case_2",
            "name": "Увеличение конверсии из КЭВа в оплату",
            "description": "Проведение расследования по текущей ситуации, усиление КЭВа, внедрение точек касания по оборудованию. Целевой показатель: конверсия с 12% до 20%.",
            "sections": {
                "a. Детали инициативы": "Описание инициативы и ответственные",
                "b. Финансовое влияние": "Финансовое влияние по годам: 120М руб (2025), 240М руб (2026), 480М руб (2027)",
                "c. Поддерживающие расчеты": "Расчет увеличения конверсии с 12% до 20%",
                "d. Диаграмма Ганта": "План выполнения: расследование, разработка скрипта, контроль",
                "e. Мониторинг эффекта": "Ежемесячный мониторинг конверсии и выручки",
                "f. Статус инициатив": "Текущий статус реализации и прогресс"
            },
            "status": "L2",
            "owner": "РОП офис Москва",
            "department": "Продажи и сервис",
            "start_date": "2025-05-12",
            "end_date": "2025-12-01",
            "last_updated": today,
            "created_date": "2025-04-01",
            "target_revenue": "120 млн руб (2025), 240 млн руб (2026), 480 млн руб (2027)",
            "key_metrics": "Конверсия КЭВ→оплата: 12%→20% (+8%)"
        }
        
    if os.path.exists("/Users/Vasily_Lukin/Downloads/Бизнес_кейс. Руслан Амерханов.xlsx"):
        projects["business_case_3"] = {
            "id": "business_case_3", 
            "name": "Увеличение конверсии из лида в запись",
            "description": "Проведение расследования, введение скрипта, ролевые игры и обучение менеджеров для повышения конверсии консультаций. Целевая конверсия: с 30% до 40%.",
            "sections": {
                "a. Детали инициативы": "Расследование, скрипты, обучение менеджеров",
                "b. Финансовое влияние": "Выручка: 35 млн руб (2025), 80 млн руб (2026), 100 млн руб (2027)",
                "c. Поддерживающие расчеты": "Повышение конверсии консультаций с 30% до 40%",
                "d. Диаграмма Ганта": "Ввод скрипта, анализ причин отвала, контроль соблюдения",
                "e. Мониторинг эффекта": "План роста конверсии: 25%→30%→35%→38%",
                "f. Статус инициатив": "Текущий статус реализации и прогресс"
            },
            "status": "L1",
            "owner": "Светлана (РОП)",
            "department": "Региональные продажи",
            "start_date": "2025-05-01",
            "end_date": "2025-07-30",
            "last_updated": today,
            "created_date": "2025-04-15",
            "target_revenue": "35 млн руб (2025), 80 млн руб (2026), 100 млн руб (2027)",
            "key_metrics": "Конверсия лид→запись: 30%→40% (+10%)"
        }
    
    return projects

def save_projects_database(projects_db):
    """Сохраняем базу данных проектов"""
    try:
        with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(projects_db, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Ошибка сохранения базы проектов: {e}")
        return False

def get_project_info():
    """Получаем информацию о проектах"""
    if not st.session_state.projects_database:
        st.session_state.projects_database = load_projects_database()
    
    return list(st.session_state.projects_database.values())

def create_new_project(project_data):
    """Создаем новый проект"""
    project_id = str(uuid.uuid4())
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Стандартные разделы для нового проекта
    default_sections = {
        "a. Детали инициативы": "Основная информация и описание проекта",
        "b. Финансовое влияние": "Финансовые показатели и прогнозы", 
        "c. Поддерживающие расчеты": "Расчеты и обоснования",
        "d. Диаграмма Ганта": "Планирование и временные рамки",
        "e. Мониторинг эффекта": "Отслеживание результатов",
        "f. Статус инициатив": "Текущий статус и прогресс"
    }
    
    new_project = {
        "id": project_id,
        "name": project_data["name"],
        "description": project_data["description"],
        "sections": default_sections,
        "status": project_data["status"],
        "owner": project_data["owner"],
        "department": project_data.get("department", "Не указан"),
        "start_date": project_data.get("start_date", ""),
        "end_date": project_data.get("end_date", ""),
        "last_updated": today,
        "created_date": today
    }
    
    # Добавляем в базу данных
    st.session_state.projects_database[project_id] = new_project
    
    # Создаем пустые данные для разделов
    for section_name in default_sections.keys():
        if section_name not in st.session_state.get('excel_data', {}):
            # Создаем пустую таблицу для нового раздела
            empty_df = pd.DataFrame({
                "Параметр": [""],
                "Значение": [""],
                "Комментарий": [""]
            })
            if 'excel_data' not in st.session_state:
                st.session_state.excel_data = {}
            st.session_state.excel_data[section_name] = empty_df
    
    # Сохраняем в файл
    save_projects_database(st.session_state.projects_database)
    
    # Добавляем запись в историю изменений
    add_changelog_entry(project_id, "Создание проекта", f"Создан новый проект: {project_data['name']}")
    
    return new_project

def get_column_config(df):
    """Автоматически определяем конфигурацию столбцов на основе типов данных"""
    column_config = {}
    
    for col in df.columns:
        # Преобразуем все данные в строки для избежания конфликтов типов
        column_config[col] = st.column_config.TextColumn(
            col,
            help=f"Поле: {col}",
            max_chars=1000,
        )
    
    return column_config

def save_excel_data(data_dict):
    """Сохраняем все данные обратно в Excel файл"""
    try:
        backup_file = "/Users/Vasily_Lukin/business_cases_backup.xlsx"
        
        with pd.ExcelWriter(backup_file, engine='openpyxl') as writer:
            for sheet_name, df in data_dict.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        st.success("✅ Данные успешно сохранены в резервный файл!")
        st.info(f"📁 Резервная копия: {backup_file}")
        return True
    except Exception as e:
        st.error(f"❌ Ошибка при сохранении: {e}")
        return False

def show_l_status_info():
    """Показываем информацию о L-статусах"""
    with st.expander("ℹ️ Информация о статусах инициатив (L0-L5)"):
        for status_code, status_info in L_STATUSES.items():
            st.markdown(f"**{status_code} - {status_info['name']}**: {status_info['description']}")

def show_projects_list():
    """Показываем список проектов"""
    st.title("💼 Управление бизнес-кейсами")
    st.markdown("---")
    
    # Информация о L-статусах
    show_l_status_info()
    
    # Кнопка создания нового проекта
    col1, col2, col3 = st.columns([1, 1, 3])
    with col1:
        if st.button("➕ Создать новый проект", use_container_width=True):
            st.session_state.current_view = "new_project"
            st.rerun()
    
    projects = get_project_info()
    
    if not projects:
        st.info("Проекты не найдены. Создайте первый проект!")
        return
    
    st.subheader("📋 Список проектов")
    
    # Фильтры
    col1, col2, col3 = st.columns(3)
    with col1:
        statuses = list(set([p['status'] for p in projects]))
        status_filter = st.selectbox("Фильтр по статусу", ["Все"] + statuses)
    with col2:
        owners = list(set([p['owner'] for p in projects]))
        owner_filter = st.selectbox("Фильтр по владельцу", ["Все"] + owners)
    with col3:
        departments = list(set([p.get('department', '') for p in projects if p.get('department')]))
        dept_filter = st.selectbox("Фильтр по отделу", ["Все"] + departments)
    
    # Фильтрация проектов
    filtered_projects = projects
    if status_filter != "Все":
        filtered_projects = [p for p in filtered_projects if p['status'] == status_filter]
    if owner_filter != "Все":
        filtered_projects = [p for p in filtered_projects if p['owner'] == owner_filter]
    if dept_filter != "Все":
        filtered_projects = [p for p in filtered_projects if p.get('department') == dept_filter]
    
    # Отображение проектов
    for project in filtered_projects:
        with st.container():
            # Определяем цвет статуса
            status_colors = {
                "L0": "#6c757d", "L1": "#fd7e14", "L2": "#ffc107", 
                "L3": "#007bff", "L4": "#28a745", "L5": "#20c997"
            }
            status_color = status_colors.get(project['status'], "#6c757d")
            
            status_display = f"{project['status']} - {L_STATUSES.get(project['status'], {}).get('name', project['status'])}"
            
            dates_info = ""
            if project.get('start_date') and project.get('end_date'):
                dates_info = f"📅 {project['start_date']} - {project['end_date']}"
            
            target_revenue = project.get('target_revenue', '')
            key_metrics = project.get('key_metrics', '')
            
            st.markdown(f"""
            <div style="border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 8px; background: white;">
                <h3 style="color: #0066cc; margin-top: 0;">{project['name']}</h3>
                <p style="color: #666; margin: 10px 0;">{project['description']}</p>
                <div style="display: flex; gap: 20px; margin: 15px 0; flex-wrap: wrap;">
                    <span><strong>Статус:</strong> <span style="color: {status_color};">{status_display}</span></span>
                    <span><strong>Владелец:</strong> {project['owner']}</span>
                    <span><strong>Отдел:</strong> {project.get('department', 'Не указан')}</span>
                </div>
                <div style="display: flex; gap: 20px; margin: 15px 0; flex-wrap: wrap;">
                    <span>{dates_info}</span>
                    <span><strong>Обновлено:</strong> {project['last_updated']}</span>
                </div>
                {f'<div style="margin: 15px 0; padding: 10px; background: #f8f9fa; border-radius: 4px;"><strong>🎯 Целевые показатели:</strong> {target_revenue}</div>' if target_revenue else ''}
                {f'<div style="margin: 15px 0; padding: 10px; background: #e3f2fd; border-radius: 4px;"><strong>📊 Ключевые метрики:</strong> {key_metrics}</div>' if key_metrics else ''}
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
            with col1:
                if st.button(f"📖 Открыть", key=f"open_{project['id']}"):
                    st.session_state.selected_project = project
                    st.session_state.current_view = "project_detail"
                    st.rerun()
            with col2:
                if st.button(f"✏️ Редактировать", key=f"edit_{project['id']}"):
                    st.session_state.selected_project = project
                    st.session_state.current_view = "edit_project"
                    st.rerun()
            with col3:
                if st.button(f"📜 История", key=f"history_{project['id']}"):
                    st.session_state.selected_project = project
                    st.session_state.current_view = "changelog"
                    st.rerun()

def show_new_project_form():
    """Форма создания нового проекта"""
    st.title("➕ Создание нового проекта")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Назад к списку"):
            st.session_state.current_view = "projects_list"
            st.rerun()
    
    # Информация о L-статусах
    show_l_status_info()
    
    with st.form("new_project_form"):
        st.subheader("📋 Основная информация")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Название проекта*", placeholder="Введите название проекта")
            owner = st.text_input("Владелец проекта*", placeholder="ФИО владельца")
            department = st.text_input("Отдел", placeholder="Название отдела")
            
            # L-статусы
            status_options = [f"{code} - {info['name']}" for code, info in L_STATUSES.items()]
            status_display = st.selectbox("Статус инициативы", status_options)
            status = status_display.split(" - ")[0]  # Извлекаем код статуса
        
        with col2:
            description = st.text_area("Описание проекта*", height=100, 
                                     placeholder="Краткое описание целей и задач проекта")
            
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                start_date = st.date_input("Дата начала")
            with col_date2:
                end_date = st.date_input("Дата окончания")
        
        st.markdown("### 📑 Разделы проекта")
        st.info("Автоматически будут созданы стандартные разделы: Детали инициативы, Финансовое влияние, Поддерживающие расчеты, Диаграмма Ганта, Мониторинг эффекта, Статус инициатив")
        
        # Возможность добавить дополнительные разделы
        st.markdown("#### Дополнительные разделы (опционально)")
        additional_sections = st.text_area("Дополнительные разделы", 
                                         placeholder="Введите названия дополнительных разделов (по одному на строке)",
                                         height=80)
        
        submit_button = st.form_submit_button("🚀 Создать проект", use_container_width=True)
        
        if submit_button:
            if name and owner and description:
                project_data = {
                    "name": name,
                    "description": description,
                    "status": status,
                    "owner": owner,
                    "department": department or "Не указан",
                    "start_date": start_date.strftime("%Y-%m-%d") if start_date else "",
                    "end_date": end_date.strftime("%Y-%m-%d") if end_date else ""
                }
                
                # Создаем проект
                new_project = create_new_project(project_data)
                
                # Добавляем дополнительные разделы
                if additional_sections.strip():
                    additional_list = [s.strip() for s in additional_sections.split('\n') if s.strip()]
                    for section in additional_list:
                        new_project['sections'][section] = f"Пользовательский раздел: {section}"
                
                st.success(f"✅ Проект '{name}' успешно создан!")
                st.info("Теперь вы можете открыть проект и начать заполнять данные в разделах.")
                
                # Автоматически переходим к новому проекту
                st.session_state.selected_project = new_project
                st.session_state.current_view = "project_detail"
                st.rerun()
                
            else:
                st.error("❌ Пожалуйста, заполните все обязательные поля (отмечены звездочкой *)")

def show_edit_project_form():
    """Форма редактирования проекта"""
    project = st.session_state.selected_project
    
    if not project:
        st.error("Проект не выбран")
        return
    
    st.title(f"✏️ Редактирование проекта")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Назад к списку"):
            st.session_state.current_view = "projects_list"
            st.rerun()
    
    # Информация о L-статусах
    show_l_status_info()
    
    with st.form("edit_project_form"):
        st.subheader("📋 Основная информация")
        
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Название проекта*", value=project['name'])
            owner = st.text_input("Владелец проекта*", value=project['owner'])
            department = st.text_input("Отдел", value=project.get('department', ''))
            
            # L-статусы
            status_options = [f"{code} - {info['name']}" for code, info in L_STATUSES.items()]
            current_status_display = f"{project['status']} - {L_STATUSES.get(project['status'], {}).get('name', project['status'])}"
            try:
                status_index = status_options.index(current_status_display)
            except ValueError:
                status_index = 0
            
            status_display = st.selectbox("Статус инициативы", status_options, index=status_index)
            status = status_display.split(" - ")[0]  # Извлекаем код статуса
        
        with col2:
            description = st.text_area("Описание проекта*", value=project['description'], height=100)
            
            col_date1, col_date2 = st.columns(2)
            with col_date1:
                try:
                    start_date = st.date_input("Дата начала", 
                                             value=datetime.strptime(project['start_date'], "%Y-%m-%d").date() if project.get('start_date') else None)
                except:
                    start_date = st.date_input("Дата начала")
            with col_date2:
                try:
                    end_date = st.date_input("Дата окончания",
                                           value=datetime.strptime(project['end_date'], "%Y-%m-%d").date() if project.get('end_date') else None)
                except:
                    end_date = st.date_input("Дата окончания")
        
        submit_button = st.form_submit_button("💾 Сохранить изменения", use_container_width=True)
        
        if submit_button:
            if name and owner and description:
                # Отслеживаем изменения
                changes = []
                if project['name'] != name:
                    changes.append(f"Название: '{project['name']}' → '{name}'")
                if project['description'] != description:
                    changes.append(f"Описание изменено")
                if project['status'] != status:
                    old_status = f"{project['status']} - {L_STATUSES.get(project['status'], {}).get('name', project['status'])}"
                    new_status = f"{status} - {L_STATUSES.get(status, {}).get('name', status)}"
                    changes.append(f"Статус: '{old_status}' → '{new_status}'")
                if project['owner'] != owner:
                    changes.append(f"Владелец: '{project['owner']}' → '{owner}'")
                if project.get('department', '') != department:
                    changes.append(f"Отдел: '{project.get('department', '')}' → '{department}'")
                
                # Обновляем данные проекта
                project['name'] = name
                project['description'] = description
                project['status'] = status
                project['owner'] = owner
                project['department'] = department or "Не указан"
                project['start_date'] = start_date.strftime("%Y-%m-%d") if start_date else ""
                project['end_date'] = end_date.strftime("%Y-%m-%d") if end_date else ""
                project['last_updated'] = datetime.now().strftime("%Y-%m-%d")
                
                # Сохраняем в базу данных
                st.session_state.projects_database[project['id']] = project
                save_projects_database(st.session_state.projects_database)
                
                # Записываем изменения в историю
                if changes:
                    change_details = "; ".join(changes)
                    add_changelog_entry(project['id'], "Редактирование проекта", change_details)
                
                st.success(f"✅ Проект '{name}' успешно обновлен!")
                st.session_state.current_view = "projects_list"
                st.rerun()
                
            else:
                st.error("❌ Пожалуйста, заполните все обязательные поля (отмечены звездочкой *)")

def show_changelog():
    """Показываем историю изменений проекта"""
    project = st.session_state.selected_project
    
    if not project:
        st.error("Проект не выбран")
        return
    
    st.title(f"📜 История изменений: {project['name']}")
    st.markdown("---")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("← Назад к списку"):
            st.session_state.current_view = "projects_list"
            st.rerun()
    
    # Загружаем историю изменений
    if 'changelog' not in st.session_state:
        st.session_state.changelog = load_changelog()
    
    # Фильтруем записи для текущего проекта
    project_changelog = [entry for entry in st.session_state.changelog if entry['project_id'] == project['id']]
    
    if not project_changelog:
        st.info("📝 История изменений пуста")
        return
    
    # Сортируем по дате (новые сначала)
    project_changelog.sort(key=lambda x: x['timestamp'], reverse=True)
    
    st.subheader(f"📊 Всего записей: {len(project_changelog)}")
    
    # Отображаем записи
    for entry in project_changelog:
        timestamp = datetime.fromisoformat(entry['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
        
        # Определяем иконку для типа действия
        action_icons = {
            "Создание проекта": "🆕",
            "Редактирование проекта": "✏️",
            "Изменение данных": "📝",
            "Добавление данных": "➕",
            "Удаление данных": "🗑️"
        }
        icon = action_icons.get(entry['action'], "📌")
        
        with st.container():
            st.markdown(f"""
            <div style="border-left: 4px solid #0066cc; padding: 15px; margin: 10px 0; background: #f8f9fa; border-radius: 0 5px 5px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <h4 style="margin: 0; color: #0066cc;">{icon} {entry['action']}</h4>
                    <small style="color: #666;">{timestamp}</small>
                </div>
                <p style="margin: 5px 0; color: #333;"><strong>Пользователь:</strong> {entry['user']}</p>
                <p style="margin: 5px 0; color: #333;"><strong>Детали:</strong> {entry['details']}</p>
            </div>
            """, unsafe_allow_html=True)

def show_project_detail():
    """Показываем детали выбранного проекта"""
    project = st.session_state.selected_project
    
    if not project:
        st.error("Проект не выбран")
        return
    
    # Загрузка данных Excel
    if 'excel_data' not in st.session_state:
        excel_data = load_excel_data()
        if excel_data:
            st.session_state.excel_data = excel_data
        else:
            st.session_state.excel_data = {}
    
    # Заголовок с навигацией
    col1, col2, col3, col4 = st.columns([1, 1, 1, 2])
    with col1:
        if st.button("← Назад к списку"):
            st.session_state.current_view = "projects_list"
            st.rerun()
    with col2:
        if st.button("✏️ Редактировать проект"):
            st.session_state.current_view = "edit_project"
            st.rerun()
    with col3:
        if st.button("📜 История изменений"):
            st.session_state.current_view = "changelog"
            st.rerun()
    
    st.title(f"💼 {project['name']}")
    st.markdown(f"*{project['description']}*")
    
    # Информация о проекте
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        status_display = f"{project['status']} - {L_STATUSES.get(project['status'], {}).get('name', project['status'])}"
        st.metric("Статус", status_display)
    with col2:
        st.metric("Владелец", project['owner'])
    with col3:
        st.metric("Отдел", project.get('department', 'Не указан'))
    with col4:
        st.metric("Последнее обновление", project['last_updated'])
    
    st.markdown("---")
    
    # Боковая панель с разделами проекта
    st.sidebar.header("📑 Разделы проекта")
    
    sections = list(project['sections'].keys())
    if not st.session_state.selected_section:
        st.session_state.selected_section = sections[0]
    
    # Создаем упрощенные названия для селектбокса
    section_display_names = []
    for section in sections:
        display_name = section
        if "_" in section:
            parts = section.split("_")
            if len(parts) >= 3:
                display_name = "_".join(parts[3:])  # Берем все после автора
        section_display_names.append(display_name)
    
    selected_display = st.sidebar.selectbox(
        "Выберите раздел:",
        section_display_names,
        index=section_display_names.index(
            "_".join(st.session_state.selected_section.split("_")[3:]) if "_" in st.session_state.selected_section and len(st.session_state.selected_section.split("_")) >= 3 else st.session_state.selected_section
        ) if st.session_state.selected_section in sections else 0
    )
    
    # Находим соответствующий полный ключ раздела
    selected_section = sections[section_display_names.index(selected_display)]
    
    st.session_state.selected_section = selected_section
    
    # Кнопки управления
    col1, col2, col3 = st.sidebar.columns(3)
    
    with col1:
        if st.button("💾 Сохранить", use_container_width=True):
            save_excel_data(st.session_state.excel_data)
    
    with col2:
        if st.button("🔄 Сбросить", use_container_width=True):
            st.session_state.excel_data = load_excel_data()
            st.rerun()
    
    with col3:
        if st.button("➕ Добавить строку", use_container_width=True):
            add_row_to_section(selected_section, project['id'])
    
    # Отображение выбранного раздела
    show_section_data(selected_section, project['sections'][selected_section], project['id'])

def add_row_to_section(section_name, project_id):
    """Добавляем строку к выбранному разделу"""
    if section_name in st.session_state.excel_data:
        current_df = st.session_state.excel_data[section_name]
        
        # Создаем новую строку с пустыми значениями
        new_row_data = {}
        for col in current_df.columns:
            new_row_data[col] = ''
        
        new_row = pd.DataFrame([new_row_data])
        st.session_state.excel_data[section_name] = pd.concat([current_df, new_row], ignore_index=True)
    else:
        # Создаем новую таблицу если раздел не существует
        empty_df = pd.DataFrame({
            "Параметр": [""],
            "Значение": [""],
            "Комментарий": [""]
        })
        st.session_state.excel_data[section_name] = empty_df
    
    # Записываем в историю изменений
    add_changelog_entry(project_id, "Добавление данных", f"Добавлена новая строка в раздел: {section_name}")
    
    st.rerun()

def show_section_data(section_name, section_description, project_id):
    """Показываем данные выбранного раздела"""
    # Упрощаем название раздела для отображения
    display_name = section_name
    if "_" in section_name:
        # Убираем префикс "Бизнес_кейс_Автор_" и оставляем только основную часть
        parts = section_name.split("_")
        if len(parts) >= 3:
            display_name = "_".join(parts[3:])  # Берем все после автора
    
    st.header(f"📄 {display_name}")
    st.info(section_description)
    
    # Ищем данные для раздела в разных вариантах ключей
    data_key = None
    potential_keys = [
        f"{project_id}_{section_name}",  # business_case_1_a. Детали инициативы
        section_name,  # a. Детали инициативы
    ]
    
    # Добавляем ключи с полными именами файлов (все используют файл Михненко)
    file_mappings = {
        "business_case_1": "Бизнес_кейс_Михненко_Екатерина",
        "business_case_2": "Бизнес_кейс_Михненко_Екатерина", 
        "business_case_3": "Бизнес_кейс_Михненко_Екатерина"
    }
    
    if project_id in file_mappings:
        full_key = f"{file_mappings[project_id]}_{section_name}"
        potential_keys.append(full_key)
    
    # Ищем данные по всем возможным ключам
    for key in potential_keys:
        if key in st.session_state.excel_data:
            data_key = key
            break
    
    if data_key is None:
        st.warning(f"Данные для раздела '{section_name}' еще не созданы. Нажмите 'Добавить строку' для начала работы.")
        
        # Показываем отладочную информацию
        with st.expander("🔍 Отладочная информация"):
            st.write("Искали данные по ключам:")
            for key in potential_keys:
                st.write(f"- {key}")
            st.write("Доступные ключи в данных:")
            for key in sorted(st.session_state.excel_data.keys()):
                st.write(f"- {key}")
        
        # Создаем пустую таблицу
        if st.button("🚀 Создать таблицу для этого раздела"):
            empty_df = pd.DataFrame({
                "Параметр": ["Название параметра"],
                "Значение": ["Значение параметра"],
                "Комментарий": ["Комментарий или описание"]
            })
            st.session_state.excel_data[section_name] = empty_df
            add_changelog_entry(project_id, "Изменение данных", f"Создана таблица для раздела: {section_name}")
            st.rerun()
        return
    
    current_df = st.session_state.excel_data[data_key]
    
    # Преобразуем все данные в строки для избежания конфликтов типов
    display_df = current_df.astype(str)
    
    # Информация о данных
    st.info(f"📊 Строк: {len(display_df)} | Столбцов: {len(display_df.columns)}")
    
    # Показываем информацию о содержимом
    with st.expander("🔍 Информация о данных"):
        col_info = []
        for col in current_df.columns:
            col_info.append({
                "Столбец": col,
                "Заполнено строк": len(current_df) - current_df[col].isnull().sum(),
                "Пример значений": str(current_df[col].dropna().iloc[0] if len(current_df[col].dropna()) > 0 else "")
            })
        st.dataframe(pd.DataFrame(col_info), use_container_width=True)
    
    # Получаем конфигурацию столбцов
    column_config = get_column_config(display_df)
    
    # Редактируемая таблица
    try:
        edited_df = st.data_editor(
            display_df,
            use_container_width=True,
            num_rows="dynamic",
            key=f"editor_{section_name}",
            column_config=column_config
        )
        
        # Проверяем на изменения
        if not edited_df.equals(display_df):
            add_changelog_entry(project_id, "Изменение данных", f"Изменены данные в разделе: {section_name}")
        
        # Обновляем данные в session state
        st.session_state.excel_data[section_name] = edited_df
        
    except Exception as e:
        st.error(f"❌ Ошибка при отображении таблицы: {e}")
        
        # Показываем таблицу только для чтения
        st.subheader("📄 Просмотр данных (только чтение)")
        st.dataframe(display_df, use_container_width=True)

def main():
    """Основная функция приложения"""
    
    # Инициализация данных при первом запуске
    if 'excel_data' not in st.session_state:
        with st.spinner("Загружаем данные из Excel файлов..."):
            st.session_state.excel_data = load_excel_data()
    
    if 'projects_database' not in st.session_state:
        with st.spinner("Загружаем базу данных проектов..."):
            st.session_state.projects_database = load_projects_database()
    
    if 'changelog' not in st.session_state:
        st.session_state.changelog = load_changelog()
    
    # Маршрутизация между экранами
    if st.session_state.current_view == "projects_list":
        show_projects_list()
    elif st.session_state.current_view == "project_detail":
        show_project_detail()
    elif st.session_state.current_view == "new_project":
        show_new_project_form()
    elif st.session_state.current_view == "edit_project":
        show_edit_project_form()
    elif st.session_state.current_view == "changelog":
        show_changelog()
    
    # Информация в сайдбаре для главного экрана
    if st.session_state.current_view == "projects_list":
        st.sidebar.markdown("---")
        with st.sidebar.expander("ℹ️ Информация"):
            st.markdown("""
            ### Управление бизнес-кейсами
            
            **Возможности:**
            - ➕ Создание новых проектов
            - 📋 Просмотр списка всех проектов
            - 🔍 Фильтрация по статусу L0-L5, владельцу, отделу
            - 📖 Детальный просмотр каждого проекта
            - ✏️ Редактирование информации о проекте
            - 📑 Работа с разделами проектов
            - 💾 Сохранение изменений
            - ➕ Добавление новых записей в разделы
            - 📜 Отслеживание истории изменений
            
            **Статусы инициатив (L0-L5):**
            - L0: Идея
            - L1: Идентифицировано
            - L2: Планирование
            - L3: Исполнение
            - L4: Завершено
            - L5: Реализовано
            
            **Как использовать:**
            1. Создайте новый проект или выберите существующий
            2. Заполните основную информацию
            3. Работайте с разделами проекта
            4. Добавляйте данные в таблицы
            5. Отслеживайте изменения в истории
            6. Сохраняйте изменения
            """)

if __name__ == "__main__":
    main() 