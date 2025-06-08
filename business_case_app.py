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

# Новые Excel файлы
EXCEL_FILES = [
    "Бизнес_кейс_Михненко_Екатерина.xlsx",
    "Бизнес_кейс_Зырянова.xlsx",
    "Бизнес_кейс. Руслан Амерханов.xlsx"
]
PROJECTS_FILE = "projects_database.json"
CHANGELOG_FILE = "changelog.json"

# L-статусы с описаниями
L_STATUSES = {
    "L0": {"name": "Идея", "description": "Сбор всех идей, независимо от реализуемости или масштаба"},
    "L1": {"name": "Идентифицировано", "description": "Инициатива признана перспективной, проводится первичная оценка и уточнение"},
    "L2": {"name": "Планирование", "description": "Разработка подробного бизнес-кейса, утверждение инициативы"},
    "L3": {"name": "Исполнение", "description": "Реализация инициативы по утвержденному плану, выполнение ключевых мероприятий"},
    "L4": {"name": "Завершено", "description": "Все шаги по реализации завершены, идет проверка достижения целевых показателей"},
    "L5": {"name": "Реализовано", "description": "Фактическая ценность подтверждена в бизнес-результатах"}
}

# Проекты с информацией
PROJECTS_INFO = {
    "business_case_1": {
        "name": "Династия Врачей - Увеличение выручки",
        "owner": "Екатерина Михайленко", 
        "description": "Увеличение выручки сети медицинских клиник через цифровизацию процессов",
        "status": "L3",
        "file": "Бизнес_кейс_Михненко_Екатерина.xlsx"
    },
    "business_case_2": {
        "name": "КЭВ - Конверсия клиентов",
        "owner": "Зырянова",
        "description": "Повышение конверсии клиентов в компании КЭВ через оптимизацию процессов", 
        "status": "L2",
        "file": "Бизнес_кейс_Зырянова.xlsx"
    },
    "business_case_3": {
        "name": "Lead to Appointment - Конверсия",
        "owner": "Руслан Амерханов",
        "description": "Увеличение конверсии лидов в записи на приемы",
        "status": "L4", 
        "file": "Бизнес_кейс. Руслан Амерханов.xlsx"
    }
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
            "Династия Врачей - Увеличение выручки",
            "КЭВ - Конверсия клиентов", 
            "Lead to Appointment - Конверсия"
        ],
        "Статус": ["L3", "L2", "L4"],
        "Владелец": [
            "Екатерина Михайленко",
            "Зырянова", 
            "Руслан Амерханов"
        ],
        "Прогресс (%)": [75, 45, 90],
        "Плановый эффект (млн руб)": [35, 120, 35],
        "Фактический эффект (млн руб)": [28, 0, 30],
        "Дата начала": [
            "2024-01-15", "2024-03-01", "2024-02-01"
        ],
        "Планируемое завершение": [
            "2024-12-31", "2025-01-31", "2024-11-30"
        ],
        "Ключевые вехи": [
            "Цифровизация процессов, увеличение доходимости",
            "Анализ КЭВ, усиление процессов",
            "Ролевки, обучение менеджеров"
        ],
        "Риски": [
            "Сопротивление изменениям",
            "Сложность процессов",
            "Высокая текучесть кадров"
        ],
        "Комментарии": [
            "Результаты превышают ожидания",
            "Требуется дополнительный анализ",
            "Обучение в процессе"
        ]
    })
    return status_data

@st.cache_data
def load_excel_data():
    """Загружаем все листы из Excel файлов"""
    all_data = {}
    
    for excel_file in EXCEL_FILES:
        try:
            if os.path.exists(excel_file):
                excel_data = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl')
                filename = os.path.basename(excel_file).replace('.xlsx', '')
                
                # Определяем project_id по файлу
                if "Михненко" in excel_file:
                    project_id = "business_case_1"
                elif "Зырянова" in excel_file:
                    project_id = "business_case_2"
                elif "Амерханов" in excel_file:
                    project_id = "business_case_3"
                else:
                    project_id = f"project_{len(all_data) + 1}"
                
                for sheet_name, df in excel_data.items():
                    # Очищаем и нормализуем данные
                    cleaned_df = df.copy()
                    
                    # Удаляем полностью пустые строки и столбцы
                    cleaned_df = cleaned_df.dropna(how='all').dropna(axis=1, how='all')
                    
                    # Переименовываем проблематичные колонки
                    new_columns = []
                    for i, col in enumerate(cleaned_df.columns):
                        col_str = str(col)
                        if col_str.startswith('Unnamed:') or col_str.isdigit() or col_str in ['nan', 'None'] or col_str.strip() == '':
                            # Даем осмысленные названия
                            if sheet_name == "a. Детали инициативы":
                                new_columns.append(f"Поле_{i+1}")
                            elif sheet_name == "b. Финансовое влияние":
                                new_columns.append(f"Финансы_{i+1}")
                            else:
                                new_columns.append(f"Столбец_{i+1}")
                        else:
                            new_columns.append(col_str)
                    
                    cleaned_df.columns = new_columns
                    
                    # Очищаем от пустых значений и преобразуем в строки
                    cleaned_df = cleaned_df.fillna('')
                    for col in cleaned_df.columns:
                        try:
                            cleaned_df[col] = cleaned_df[col].astype(str)
                            cleaned_df[col] = cleaned_df[col].replace('nan', '')
                            cleaned_df[col] = cleaned_df[col].replace('None', '')
                            cleaned_df[col] = cleaned_df[col].replace('<NA>', '')
                        except:
                            cleaned_df[col] = ''
                    
                    # Удаляем строки где все значения пустые
                    mask = cleaned_df.apply(lambda row: all(str(val).strip() == '' for val in row), axis=1)
                    cleaned_df = cleaned_df[~mask]
                    
                    # Если данных недостаточно, дополняем базовой структурой
                    if len(cleaned_df) == 0:
                        if sheet_name == "a. Детали инициативы":
                            cleaned_df = pd.DataFrame({
                                "Параметр": ["Название инициативы", "Описание инициативы", "Ответственный за инициативу"],
                                "Значение": ["", "", ""],
                                "Комментарий": ["", "", ""]
                            })
                        else:
                            cleaned_df = pd.DataFrame({
                                "Параметр": [""],
                                "Значение": [""],
                                "Комментарий": [""]
                            })
                    
                    # Сохраняем данные с ключом проекта и раздела
                    section_key = f"{project_id}_{sheet_name}"
                    all_data[section_key] = cleaned_df.copy()
                    
                    # Также сохраняем под простым названием раздела для обратной совместимости
                    all_data[sheet_name] = cleaned_df.copy()
                
                st.success(f"✅ Загружен файл: {filename}")
                
        except Exception as e:
            st.error(f"❌ Не удалось загрузить файл {excel_file}: {e}")
            continue
    
    # Если ничего не загрузилось, создаем пустые данные
    if not all_data:
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
                "Параметр": ["Данные не загружены"],
                "Значение": ["Проверьте наличие Excel файлов"],
                "Комментарий": [""]
            })
            all_data[section] = empty_df
    
    return all_data

def load_changelog():
    """Загружаем журнал изменений"""
    try:
        if os.path.exists(CHANGELOG_FILE):
            with open(CHANGELOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except:
        return []

def save_changelog(changelog):
    """Сохраняем журнал изменений"""
    try:
        with open(CHANGELOG_FILE, 'w', encoding='utf-8') as f:
            json.dump(changelog, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def add_changelog_entry(project_id, action, details, user="Текущий пользователь"):
    """Добавляем запись в журнал изменений"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "project_id": project_id,
        "user": user,
        "action": action,
        "details": details
    }
    
    changelog = load_changelog()
    changelog.append(entry)
    save_changelog(changelog)
    
    # Обновляем состояние
    st.session_state.changelog = changelog

def load_projects_database():
    """Загружаем базу проектов"""
    try:
        if os.path.exists(PROJECTS_FILE):
            with open(PROJECTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Создаем начальную базу из PROJECTS_INFO
            return PROJECTS_INFO.copy()
    except:
        return PROJECTS_INFO.copy()

def save_projects_database(projects_db):
    """Сохраняем базу проектов"""
    try:
        with open(PROJECTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(projects_db, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def get_project_info():
    """Получаем информацию о проектах"""
    return load_projects_database()

def create_new_project(project_data):
    """Создаем новый проект"""
    projects_db = load_projects_database()
    
    # Генерируем новый ID
    new_id = f"business_case_{len(projects_db) + 1}"
    
    # Добавляем проект
    projects_db[new_id] = project_data
    
    # Сохраняем
    if save_projects_database(projects_db):
        st.session_state.projects_database = projects_db
        add_changelog_entry(new_id, "Создание проекта", f"Создан новый проект: {project_data['name']}")
        return new_id
    return None

def get_column_config(df):
    """Создаем конфигурацию колонок для data_editor"""
    config = {}
    for col in df.columns:
        config[col] = st.column_config.TextColumn(
            col,
            help=f"Редактируемое поле: {col}",
            max_chars=500,
            width="medium"
        )
    return config

def save_excel_data(data_dict):
    """Сохраняем изменения обратно в Excel (заглушка)"""
    # В реальной реализации здесь можно сохранять в Excel
    st.success("✅ Изменения сохранены в памяти")
    return True

def show_l_status_info():
    """Показываем информацию о L-статусах"""
    st.markdown("### 📊 L-статусы проектов")
    
    for status, info in L_STATUSES.items():
        with st.expander(f"{status}: {info['name']}"):
            st.write(info['description'])

def show_projects_list():
    """Показываем список всех проектов"""
    st.title("💼 Управление бизнес-кейсами")
    st.markdown("---")
    
    # Кнопки навигации
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("📝 Новый проект"):
            st.session_state.current_view = "new_project"
            st.rerun()
    
    with col2:
        if st.button("📊 Статистика"):
            st.session_state.current_view = "analytics"
            st.rerun()
    
    with col3:
        if st.button("📋 Журнал изменений"):
            st.session_state.current_view = "changelog"
            st.rerun()
    
    with col4:
        if st.button("🔄 Обновить данные"):
            st.cache_data.clear()
            st.rerun()
    
    # Загружаем проекты
    projects_db = get_project_info()
    
    if not projects_db:
        st.warning("📭 Нет созданных проектов")
        return
    
    # Группируем проекты по L-статусам
    st.markdown("### 📊 Проекты по L-статусам")
    
    # Создаем вкладки для каждого L-статуса
    status_tabs = st.tabs([f"{status}: {info['name']}" for status, info in L_STATUSES.items()])
    
    for i, (status, status_info) in enumerate(L_STATUSES.items()):
        with status_tabs[i]:
            st.markdown(f"**{status_info['description']}**")
            
            # Фильтруем проекты по статусу
            status_projects = {k: v for k, v in projects_db.items() if v.get('status') == status}
            
            if status_projects:
                for project_id, project_info in status_projects.items():
                    with st.container():
                        col1, col2, col3 = st.columns([3, 1, 1])
                        
                        with col1:
                            st.markdown(f"**{project_info['name']}**")
                            st.caption(f"👤 {project_info['owner']}")
                            st.caption(project_info['description'])
                        
                        with col2:
                            status_color = {
                                "L0": "🔴", "L1": "🟠", "L2": "🟡",
                                "L3": "🟢", "L4": "🔵", "L5": "🟣"
                            }
                            st.markdown(f"### {status_color.get(status, '⚪')} {status}")
                        
                        with col3:
                            if st.button("📋 Открыть", key=f"open_{project_id}"):
                                st.session_state.selected_project = project_id
                                st.session_state.current_view = "project_detail"
                                st.rerun()
                        
                        st.markdown("---")
            else:
                st.info(f"📭 Нет проектов со статусом {status}")
    
    # Показываем сводную информацию
    st.markdown("### 📈 Сводная информация")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Всего проектов", len(projects_db))
    
    with col2:
        active_projects = len([p for p in projects_db.values() if p.get('status') in ['L1', 'L2', 'L3']])
        st.metric("Активных проектов", active_projects)
    
    with col3:
        completed_projects = len([p for p in projects_db.values() if p.get('status') in ['L4', 'L5']])
        st.metric("Завершенных проектов", completed_projects)

def show_new_project_form():
    """Форма создания нового проекта"""
    st.title("📝 Создание нового проекта")
    
    if st.button("⬅️ Назад к списку"):
        st.session_state.current_view = "projects_list"
        st.rerun()
    
    st.markdown("---")
    
    with st.form("new_project_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("📋 Название проекта *")
            owner = st.text_input("👤 Владелец проекта *")
            status = st.selectbox("📊 L-статус", options=list(L_STATUSES.keys()),
                                format_func=lambda x: f"{x}: {L_STATUSES[x]['name']}")
        
        with col2:
            description = st.text_area("📝 Описание проекта *", height=100)
            file_option = st.selectbox("📁 Excel файл", ["Создать новый"] + EXCEL_FILES)
            
        submitted = st.form_submit_button("✅ Создать проект", type="primary")
        
        if submitted:
            if not name or not owner or not description:
                st.error("❌ Заполните все обязательные поля")
            else:
                project_data = {
                    "name": name,
                    "owner": owner,
                    "description": description,
                    "status": status,
                    "file": file_option if file_option != "Создать новый" else None,
                    "created_date": datetime.now().isoformat(),
                    "updated_date": datetime.now().isoformat()
                }
                
                new_id = create_new_project(project_data)
                if new_id:
                    st.success(f"✅ Проект создан с ID: {new_id}")
                    st.session_state.selected_project = new_id
                    st.session_state.current_view = "project_detail"
                    st.rerun()
                else:
                    st.error("❌ Ошибка при создании проекта")

def show_project_detail():
    """Показываем детали проекта"""
    if not st.session_state.selected_project:
        st.error("❌ Проект не выбран")
        return
    
    project_id = st.session_state.selected_project
    projects_db = get_project_info()
    
    if project_id not in projects_db:
        st.error("❌ Проект не найден")
        return
    
    project_info = projects_db[project_id]
    
    # Заголовок
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"🎯 {project_info['name']}")
        st.caption(f"👤 Владелец: {project_info['owner']}")
    
    with col2:
        if st.button("⬅️ К списку проектов"):
            st.session_state.current_view = "projects_list"
            st.rerun()
    
    # Информация о проекте
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = project_info.get('status', 'L0')
        status_color = {
            "L0": "🔴", "L1": "🟠", "L2": "🟡",
            "L3": "🟢", "L4": "🔵", "L5": "🟣"
        }
        st.markdown(f"**Статус:** {status_color.get(status, '⚪')} {status} - {L_STATUSES[status]['name']}")
    
    with col2:
        if 'created_date' in project_info:
            created = datetime.fromisoformat(project_info['created_date']).strftime("%d.%m.%Y")
            st.markdown(f"**Создан:** {created}")
    
    with col3:
        if 'updated_date' in project_info:
            updated = datetime.fromisoformat(project_info['updated_date']).strftime("%d.%m.%Y")
            st.markdown(f"**Обновлен:** {updated}")
    
    st.markdown(f"**Описание:** {project_info['description']}")
    st.markdown("---")
    
    # Загружаем данные
    data_dict = load_excel_data()
    
    # Разделы проекта
    sections = [
        ("a. Детали инициативы", "📋 Основная информация о проекте"),
        ("b. Финансовое влияние", "💰 Финансовые показатели и ROI"),
        ("c. Поддерживающие расчеты", "🧮 Детальные расчеты"),
        ("d. Диаграмма Ганта", "📅 Временные рамки проекта"),
        ("e. Мониторинг эффекта", "📈 Отслеживание результатов"),
        ("f. Статус инициатив", "🎯 Текущий статус")
    ]
    
    # Создаем вкладки для разделов
    section_tabs = st.tabs([f"{section[0]}" for section in sections])
    
    for i, (section_name, section_desc) in enumerate(sections):
        with section_tabs[i]:
            show_section_data(section_name, section_desc, project_id, data_dict)

def show_section_data(section_name, section_description, project_id, data_dict):
    """Показываем данные раздела с возможностью редактирования"""
    st.subheader(section_description)
    
    # Ищем данные для этого раздела и проекта
    section_key = f"{project_id}_{section_name}"
    
    if section_key in data_dict:
        df = data_dict[section_key].copy()
    elif section_name in data_dict:
        df = data_dict[section_name].copy()
    else:
        # Создаем пустой DataFrame
        df = pd.DataFrame({
            "Параметр": [""],
            "Значение": [""],
            "Комментарий": [""]
        })
    
    if df.empty:
        st.warning(f"⚠️ Данные для раздела '{section_name}' еще не созданы")
        if st.button(f"➕ Создать данные для '{section_name}'", key=f"create_{section_name}"):
            # Создаем базовую структуру
            df = pd.DataFrame({
                "Параметр": ["Новый параметр"],
                "Значение": ["Новое значение"],
                "Комментарий": [""]
            })
    
    # Кнопки управления
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button(f"➕ Добавить строку", key=f"add_row_{section_name}"):
            new_row = pd.DataFrame({col: [""] for col in df.columns}, index=[len(df)])
            df = pd.concat([df, new_row], ignore_index=True)
    
    with col2:
        if st.button(f"🔄 Обновить данные", key=f"refresh_{section_name}"):
            st.cache_data.clear()
            st.rerun()
    
    with col3:
        if st.button(f"💾 Сохранить изменения", key=f"save_{section_name}"):
            save_excel_data({section_key: df})
            add_changelog_entry(project_id, "Изменение данных", f"Обновлен раздел: {section_name}")
    
    # Редактор данных
    if not df.empty:
        try:
            edited_df = st.data_editor(
                df,
                use_container_width=True,
                num_rows="dynamic",
                column_config=get_column_config(df),
                key=f"editor_{project_id}_{section_name}"
            )
            
            # Показываем количество строк
            st.caption(f"📊 Строк в таблице: {len(edited_df)}")
            
        except Exception as e:
            st.error(f"❌ Ошибка отображения данных: {e}")
            st.dataframe(df, use_container_width=True)

def show_changelog():
    """Показываем журнал изменений"""
    st.title("📋 Журнал изменений")
    
    if st.button("⬅️ Назад к списку"):
        st.session_state.current_view = "projects_list"
        st.rerun()
    
    changelog = load_changelog()
    
    if not changelog:
        st.info("📭 Журнал изменений пуст")
        return
    
    # Сортируем по дате (новые сверху)
    changelog_sorted = sorted(changelog, key=lambda x: x['timestamp'], reverse=True)
    
    for entry in changelog_sorted:
        with st.container():
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                st.markdown(f"**{entry['action']}**")
                st.caption(entry['details'])
            
            with col2:
                timestamp = datetime.fromisoformat(entry['timestamp'])
                st.caption(f"🕒 {timestamp.strftime('%d.%m.%Y %H:%M')}")
            
            with col3:
                st.caption(f"👤 {entry['user']}")
                if 'project_id' in entry:
                    st.caption(f"📁 {entry['project_id']}")
            
            st.markdown("---")

def main():
    """Главная функция приложения"""
    
    # Инициализация данных в состоянии
    if 'projects_database' not in st.session_state or not st.session_state.projects_database:
        st.session_state.projects_database = get_project_info()
    
    if 'changelog' not in st.session_state or not st.session_state.changelog:
        st.session_state.changelog = load_changelog()
    
    # Боковая панель с информацией о L-статусах
    with st.sidebar:
        show_l_status_info()
        
        st.markdown("---")
        st.markdown("### ℹ️ Информация о системе")
        st.markdown(f"**Проектов в системе:** {len(st.session_state.projects_database)}")
        st.markdown(f"**Записей в журнале:** {len(st.session_state.changelog)}")
        st.markdown(f"**Последнее обновление:** {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    
    # Основное содержимое
    if st.session_state.current_view == "projects_list":
        show_projects_list()
    elif st.session_state.current_view == "project_detail":
        show_project_detail()
    elif st.session_state.current_view == "new_project":
        show_new_project_form()
    elif st.session_state.current_view == "changelog":
        show_changelog()
    else:
        show_projects_list()

if __name__ == "__main__":
    main() 