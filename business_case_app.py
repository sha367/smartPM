import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta
import uuid
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

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
    
    # Создаем метрики
    col1, col2, col3, col4 = st.columns(4)
    
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
    
    with col4:
        # Средняя конверсия
        avg_conversion = 0
        conversion_count = 0
        for project_data in all_projects_data.values():
            calc_data = project_data["data"].get("c. Поддерживающие расчеты", pd.DataFrame())
            if not calc_data.empty and "Будущее состояние" in calc_data.columns:
                try:
                    conv = float(calc_data["Будущее состояние"].iloc[0]) if len(calc_data) > 0 else 0
                    if conv > 0:
                        avg_conversion += conv
                        conversion_count += 1
                except:
                    pass
        if conversion_count > 0:
            avg_conversion = avg_conversion / conversion_count
        st.metric("Средняя целевая конверсия", f"{avg_conversion:.1%}")
    
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
    st.caption("Система управления бизнес-кейсами v3.0")
    
    # Боковая панель с навигацией
    with st.sidebar:
        st.header("🧭 Навигация")
        
        page = st.selectbox(
            "Выберите страницу:",
            ["📊 Сводная дашборд", "📋 Проекты"]
        )
        
        if page == "📋 Проекты":
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
    elif page == "📋 Проекты" and selected_project:
        show_project_details(selected_project)
    else:
        st.info("👈 Выберите страницу в боковой панели")

if __name__ == "__main__":
    main() 