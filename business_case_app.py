import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import uuid
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import tempfile
import shutil

# Конфигурация страницы
st.set_page_config(
    page_title="🎯 Business Case Manager",
    page_icon="🎯", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Константы
EXCEL_FILES = {
    "mikhailenko": {
        "file": "Бизнес_кейс_Михненко_Екатерина.xlsx",
        "name": "Династия Врачей - Увеличение выручки",
        "owner": "Екатерина Михненко",
        "description": "Достичь плановой выручки 35 млн рублей за счёт повышения доходимости"
    },
    "zyryanova": {
        "file": "Бизнес_кейс_Зырянова.xlsx", 
        "name": "Увеличение конверсии из КЭВа в оплату",
        "owner": "Зырянова",
        "description": "Проведение расследования по текущей ситуации, усиление КЭВа"
    },
    "amerkhanov": {
        "file": "Бизнес_кейс. Руслан Амерханов.xlsx",
        "name": "Увеличение конверсии из лида в запись", 
        "owner": "Руслан Амерханов",
        "description": "Проведение расследования, введение скрипта, ролевки и обучение менеджеров"
    }
}

SECTION_NAMES = {
    "a. Детали инициативы": {
        "icon": "📋",
        "description": "Основная информация об инициативе"
    },
    "b. Финансовое влияние": {
        "icon": "💰", 
        "description": "Финансовые показатели и прогнозы"
    },
    "c. Поддерживающие расчеты": {
        "icon": "📊",
        "description": "Расчеты и аналитика"
    },
    "d. Диаграмма Ганта": {
        "icon": "📅",
        "description": "Временной план проекта"
    },
    "e. Мониторинг эффекта": {
        "icon": "📈",
        "description": "Отслеживание результатов"
    },
    "f. Статус инициатив": {
        "icon": "⚡",
        "description": "Текущий статус проекта"
    }
}

# Функции загрузки данных
@st.cache_data
def load_business_case_data(business_case_id):
    """Загружаем данные конкретного бизнес-кейса"""
    if business_case_id not in EXCEL_FILES:
        return None
    
    file_info = EXCEL_FILES[business_case_id]
    file_path = file_info["file"]
    
    if not os.path.exists(file_path):
        st.error(f"❌ Файл {file_path} не найден")
        return None
    
    try:
        # Читаем все листы
        excel_data = pd.read_excel(file_path, sheet_name=None)
        
        # Обрабатываем каждый лист
        processed_data = {}
        for sheet_name, df in excel_data.items():
            # Очищаем данные
            clean_df = clean_dataframe(df)
            processed_data[sheet_name] = clean_df
            
        return {
            "data": processed_data,
            "meta": file_info,
            "file_path": file_path
        }
        
    except Exception as e:
        st.error(f"❌ Ошибка загрузки {file_path}: {e}")
        return None

def clean_dataframe(df):
    """Очищаем и нормализуем DataFrame"""
    if df.empty:
        return df
    
    # Заменяем NaN на пустые строки
    df = df.fillna('')
    
    # Преобразуем все в строки для совместимости с data_editor
    for col in df.columns:
        df[col] = df[col].astype(str)
        df[col] = df[col].replace(['nan', 'None', '<NA>'], '')
    
    # Переименовываем проблематичные колонки
    new_columns = []
    for i, col in enumerate(df.columns):
        col_str = str(col)
        if col_str.startswith('Unnamed:') or col_str.isdigit():
            new_columns.append(f"Столбец_{i+1}")
        else:
            new_columns.append(col_str)
    
    df.columns = new_columns
    
    return df

def create_summary_dashboard():
    """Создаем сводную дашборд по всем проектам"""
    st.header("📊 Сводная дашборд по всем проектам")
    
    # Загружаем данные всех проектов
    all_projects_data = {}
    for project_id in EXCEL_FILES.keys():
        data = load_business_case_data(project_id)
        if data:
            all_projects_data[project_id] = data
    
    if not all_projects_data:
        st.warning("⚠️ Нет данных для отображения")
        return
    
    # Создаем метрики (убрали конверсию)
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Всего проектов", len(all_projects_data))
    
    with col2:
        # Считаем общий финансовый эффект
        total_effect_2025 = 0
        for project_data in all_projects_data.values():
            finance_data = project_data["data"].get("b. Финансовое влияние", pd.DataFrame())
            if not finance_data.empty and "2025" in finance_data.columns:
                try:
                    effect = float(finance_data["2025"].iloc[0]) if len(finance_data) > 0 else 0
                    total_effect_2025 += effect
                except:
                    pass
        st.metric("Общий эффект 2025", f"{total_effect_2025} млн ₽")
    
    with col3:
        # Считаем эффект 2026
        total_effect_2026 = 0
        for project_data in all_projects_data.values():
            finance_data = project_data["data"].get("b. Финансовое влияние", pd.DataFrame())
            if not finance_data.empty and "2026" in finance_data.columns:
                try:
                    effect = float(finance_data["2026"].iloc[0]) if len(finance_data) > 0 else 0
                    total_effect_2026 += effect
                except:
                    pass
        st.metric("Общий эффект 2026", f"{total_effect_2026} млн ₽")
    
    # График финансового эффекта
    st.subheader("💰 Финансовый эффект по годам")
    
    years = ["2025", "2026", "2027"]
    chart_data = []
    
    for project_id, project_data in all_projects_data.items():
        project_name = EXCEL_FILES[project_id]["name"]
        finance_data = project_data["data"].get("b. Финансовое влияние", pd.DataFrame())
        
        for year in years:
            if not finance_data.empty and year in finance_data.columns:
                try:
                    value = float(finance_data[year].iloc[0]) if len(finance_data) > 0 else 0
                    chart_data.append({
                        "Проект": project_name,
                        "Год": year,
                        "Эффект (млн ₽)": value
                    })
                except:
                    chart_data.append({
                        "Проект": project_name,
                        "Год": year,
                        "Эффект (млн ₽)": 0
                    })
    
    if chart_data:
        chart_df = pd.DataFrame(chart_data)
        fig = px.bar(chart_df, x="Год", y="Эффект (млн ₽)", 
                     color="Проект", title="Финансовый эффект по проектам и годам")
        st.plotly_chart(fig, use_container_width=True)
    
    # Таблица с деталями проектов
    st.subheader("📋 Детали проектов")
    
    projects_summary = []
    for project_id, project_data in all_projects_data.items():
        project_info = EXCEL_FILES[project_id]
        details_data = project_data["data"].get("a. Детали инициативы", pd.DataFrame())
        
        if not details_data.empty:
            initiative_name = details_data.iloc[0, 0] if len(details_data) > 0 else "Не указано"
            description = details_data.iloc[0, 1] if len(details_data.columns) > 1 else "Не указано"
            responsible = details_data.iloc[0, 2] if len(details_data.columns) > 2 else "Не указано"
        else:
            initiative_name = project_info["name"]
            description = project_info["description"]
            responsible = project_info["owner"]
        
        projects_summary.append({
            "Проект": initiative_name,
            "Описание": description[:100] + "..." if len(description) > 100 else description,
            "Ответственный": responsible,
            "Владелец": project_info["owner"]
        })
    
    if projects_summary:
        summary_df = pd.DataFrame(projects_summary)
        st.dataframe(summary_df, use_container_width=True)

def show_project_management():
    """Страница управления проектами"""
    st.header("📋 Управление проектами")
    
    tabs = st.tabs(["📝 Список проектов", "➕ Добавить проект", "🗑️ Управление проектами"])
    
    with tabs[0]:
        show_projects_list()
    
    with tabs[1]:
        show_add_project_form()
    
    with tabs[2]:
        show_project_management_tools()

def show_projects_list():
    """Показываем список всех проектов"""
    st.subheader("📝 Список всех проектов")
    
    projects_data = []
    for project_id, project_info in EXCEL_FILES.items():
        # Пытаемся загрузить данные
        data = load_business_case_data(project_id)
        status = "✅ Загружен" if data else "❌ Ошибка"
        
        projects_data.append({
            "ID": project_id,
            "Название": project_info["name"],
            "Владелец": project_info["owner"],
            "Описание": project_info["description"][:50] + "...",
            "Файл": project_info["file"],
            "Статус": status
        })
    
    if projects_data:
        df = pd.DataFrame(projects_data)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("📭 Нет проектов для отображения")

def show_add_project_form():
    """Форма добавления нового проекта"""
    st.subheader("➕ Добавить новый проект")
    
    with st.form("add_project_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            project_name = st.text_input("📋 Название проекта *", 
                                       placeholder="Введите название проекта")
            project_owner = st.text_input("👤 Владелец проекта *",
                                        placeholder="ФИО владельца")
            
        with col2:
            project_description = st.text_area("📝 Описание проекта *",
                                             placeholder="Краткое описание проекта",
                                             height=100)
        
        uploaded_file = st.file_uploader("📎 Excel файл с данными",
                                       type=['xlsx', 'xls'],
                                       help="Загрузите Excel файл с структурой бизнес-кейса")
        
        submitted = st.form_submit_button("✅ Добавить проект", type="primary")
        
        if submitted:
            if not project_name or not project_owner or not project_description:
                st.error("❌ Заполните все обязательные поля")
            elif not uploaded_file:
                st.error("❌ Загрузите Excel файл")
            else:
                # Создаем новый проект
                success = add_new_project(project_name, project_owner, project_description, uploaded_file)
                if success:
                    st.success("✅ Проект успешно добавлен!")
                    st.rerun()
                else:
                    st.error("❌ Ошибка при добавлении проекта")

def add_new_project(name, owner, description, uploaded_file):
    """Добавляем новый проект"""
    try:
        # Генерируем уникальный ID
        project_id = f"project_{uuid.uuid4().hex[:8]}"
        
        # Сохраняем загруженный файл
        file_extension = uploaded_file.name.split('.')[-1]
        filename = f"Бизнес_кейс_{owner.replace(' ', '_')}.{file_extension}"
        
        with open(filename, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Добавляем в словарь проектов
        global EXCEL_FILES
        EXCEL_FILES[project_id] = {
            "file": filename,
            "name": name,
            "owner": owner,
            "description": description
        }
        
        # Очищаем кэш чтобы новые данные загрузились
        st.cache_data.clear()
        
        return True
        
    except Exception as e:
        st.error(f"Ошибка при добавлении проекта: {e}")
        return False

def show_project_management_tools():
    """Инструменты управления проектами"""
    st.subheader("🗑️ Управление проектами")
    
    if not EXCEL_FILES:
        st.info("📭 Нет проектов для управления")
        return
    
    # Выбор проекта для удаления
    project_options = {
        f"{info['name']} (ID: {project_id})": project_id 
        for project_id, info in EXCEL_FILES.items()
    }
    
    selected_project_display = st.selectbox(
        "🎯 Выберите проект для управления:",
        options=list(project_options.keys())
    )
    
    if selected_project_display:
        selected_project_id = project_options[selected_project_display]
        project_info = EXCEL_FILES[selected_project_id]
        
        # Информация о проекте
        st.info(f"""
        **Название:** {project_info['name']}  
        **Владелец:** {project_info['owner']}  
        **Описание:** {project_info['description']}  
        **Файл:** {project_info['file']}
        """)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Удалить проект", type="secondary"):
                success = delete_project(selected_project_id)
                if success:
                    st.success("✅ Проект удален!")
                    st.rerun()
                else:
                    st.error("❌ Ошибка при удалении")
        
        with col2:
            if st.button("🔄 Перезагрузить данные"):
                st.cache_data.clear()
                st.success("✅ Кэш очищен!")
                st.rerun()
        
        with col3:
            # Скачивание Excel файла
            if os.path.exists(project_info['file']):
                with open(project_info['file'], "rb") as file:
                    st.download_button(
                        label="📥 Скачать Excel",
                        data=file,
                        file_name=project_info['file'],
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

def delete_project(project_id):
    """Удаляем проект"""
    try:
        if project_id in EXCEL_FILES:
            project_info = EXCEL_FILES[project_id]
            
            # Удаляем файл если он существует
            if os.path.exists(project_info['file']):
                os.remove(project_info['file'])
            
            # Удаляем из словаря
            del EXCEL_FILES[project_id]
            
            # Очищаем кэш
            st.cache_data.clear()
            
            return True
    except Exception as e:
        st.error(f"Ошибка при удалении проекта: {e}")
        return False

def show_project_details(business_case_id):
    """Показываем детали конкретного проекта"""
    if business_case_id not in EXCEL_FILES:
        st.error("❌ Неизвестный проект")
        return
    
    project_info = EXCEL_FILES[business_case_id]
    st.header(f"🎯 {project_info['name']}")
    st.caption(f"👤 Владелец: {project_info['owner']}")
    
    # Загружаем данные проекта
    project_data = load_business_case_data(business_case_id)
    if not project_data:
        st.error("❌ Не удалось загрузить данные проекта")
        return
    
    # Показываем навигацию по разделам
    tabs = st.tabs([f"{SECTION_NAMES[section]['icon']} {section}" for section in SECTION_NAMES.keys()])
    
    for i, (section_key, section_info) in enumerate(SECTION_NAMES.items()):
        with tabs[i]:
            st.subheader(f"{section_info['icon']} {section_key}")
            st.caption(section_info['description'])
            
            # Получаем данные раздела
            section_data = project_data["data"].get(section_key, pd.DataFrame())
            
            if section_data.empty:
                st.warning(f"⚠️ Нет данных для раздела '{section_key}'")
                continue
            
            # Специальная обработка для разных разделов
            if section_key == "d. Диаграмма Ганта":
                show_gantt_chart(section_data)
            elif section_key == "e. Мониторинг эффекта":
                show_monitoring_chart(section_data)
            elif section_key == "b. Финансовое влияние":
                show_financial_impact(section_data)
            else:
                # Обычный редактор данных
                if st.button(f"🔄 Обновить данные раздела '{section_key}'", key=f"refresh_{section_key}"):
                    st.cache_data.clear()
                    st.rerun()
                
                edited_df = st.data_editor(
                    section_data,
                    use_container_width=True,
                    num_rows="dynamic",
                    key=f"editor_{business_case_id}_{section_key}"
                )
                
                if st.button(f"💾 Сохранить изменения в '{section_key}'", key=f"save_{section_key}"):
                    # Здесь можно добавить логику сохранения
                    st.success(f"✅ Изменения в разделе '{section_key}' сохранены!")

def show_gantt_chart(gantt_data):
    """Показываем диаграмму Ганта"""
    if gantt_data.empty or "Задача" not in gantt_data.columns:
        st.warning("⚠️ Недостаточно данных для построения диаграммы Ганта")
        st.dataframe(gantt_data, use_container_width=True)
        return
    
    try:
        # Преобразуем даты
        gantt_data = gantt_data.copy()
        gantt_data["Начало"] = pd.to_datetime(gantt_data["Начало"], errors='coerce')
        gantt_data["Конец"] = pd.to_datetime(gantt_data["Конец"], errors='coerce')
        
        # Создаем диаграмму Ганта
        fig = px.timeline(
            gantt_data,
            x_start="Начало",
            x_end="Конец", 
            y="Задача",
            title="📅 Диаграмма Ганта проекта"
        )
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Ошибка построения диаграммы Ганта: {e}")
    
    # Показываем таблицу данных
    st.subheader("📋 Данные проекта")
    edited_df = st.data_editor(
        gantt_data,
        use_container_width=True,
        num_rows="dynamic"
    )

def show_monitoring_chart(monitoring_data):
    """Показываем график мониторинга"""
    if monitoring_data.empty:
        st.warning("⚠️ Нет данных для мониторинга")
        return
    
    st.subheader("📈 График мониторинга")
    
    # Показываем таблицу данных
    edited_df = st.data_editor(
        monitoring_data,
        use_container_width=True,
        num_rows="dynamic"
    )
    
    # Пытаемся построить график если есть числовые данные
    try:
        numeric_cols = []
        for col in monitoring_data.columns:
            if col != monitoring_data.columns[0]:  # Пропускаем первую колонку (обычно названия)
                try:
                    pd.to_numeric(monitoring_data[col], errors='raise')
                    numeric_cols.append(col)
                except:
                    pass
        
        if numeric_cols:
            fig = go.Figure()
            for col in numeric_cols:
                fig.add_trace(go.Scatter(
                    x=monitoring_data[monitoring_data.columns[0]],
                    y=pd.to_numeric(monitoring_data[col], errors='coerce'),
                    mode='lines+markers',
                    name=col
                ))
            
            fig.update_layout(title="Динамика показателей")
            st.plotly_chart(fig, use_container_width=True)
            
    except Exception as e:
        st.info(f"ℹ️ График мониторинга недоступен: {e}")

def show_financial_impact(finance_data):
    """Показываем финансовое влияние с графиками"""
    if finance_data.empty:
        st.warning("⚠️ Нет финансовых данных")
        return
    
    # Редактор данных
    edited_df = st.data_editor(
        finance_data,
        use_container_width=True,
        num_rows="dynamic"
    )
    
    # График по годам
    if len(finance_data) > 0:
        years = ["2025", "2026", "2027"]
        year_data = []
        
        for year in years:
            if year in finance_data.columns:
                try:
                    value = float(finance_data[year].iloc[0])
                    year_data.append({"Год": year, "Эффект (млн ₽)": value})
                except:
                    year_data.append({"Год": year, "Эффект (млн ₽)": 0})
        
        if year_data:
            year_df = pd.DataFrame(year_data)
            fig = px.bar(year_df, x="Год", y="Эффект (млн ₽)", 
                        title="💰 Финансовый эффект по годам")
            st.plotly_chart(fig, use_container_width=True)

# Основная функция приложения
def main():
    st.title("🎯 Business Case Manager")
    st.caption("Система управления бизнес-кейсами v3.1")
    
    # Боковая панель с навигацией
    with st.sidebar:
        st.header("🧭 Навигация")
        
        page = st.selectbox(
            "Выберите страницу:",
            ["📊 Сводная дашборд", "📋 Управление проектами", "🎯 Просмотр проекта"]
        )
        
        if page == "🎯 Просмотр проекта":
            if EXCEL_FILES:
                st.subheader("Выберите проект:")
                project_options = {
                    f"🎯 {info['name']}": project_id 
                    for project_id, info in EXCEL_FILES.items()
                }
                
                selected_project_display = st.selectbox(
                    "Проект:",
                    options=list(project_options.keys())
                )
                
                selected_project = project_options[selected_project_display]
            else:
                st.warning("⚠️ Нет доступных проектов")
                selected_project = None
        else:
            selected_project = None
        
        # Информация о системе
        st.markdown("---")
        st.markdown("### ℹ️ Информация")
        st.markdown(f"**Проектов загружено:** {len(EXCEL_FILES)}")
        st.markdown(f"**Последнее обновление:** {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        # Кнопка обновления
        if st.button("🔄 Обновить данные"):
            st.cache_data.clear()
            st.rerun()
    
    # Основное содержимое
    if page == "📊 Сводная дашборд":
        create_summary_dashboard()
    elif page == "📋 Управление проектами":
        show_project_management()
    elif page == "🎯 Просмотр проекта" and selected_project:
        show_project_details(selected_project)
    else:
        st.info("👈 Выберите страницу в боковой панели")

if __name__ == "__main__":
    main() 