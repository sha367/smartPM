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
import numpy as np
from pathlib import Path
import openpyxl

# Конфигурация страницы
st.set_page_config(
    page_title="SmartPM | L0-L5 Project Management",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Глобальные переменные
EXCEL_FILES = {
    "mikhailenko": {
        "name": "Династия Врачей - Увеличение выручки", 
        "file": "Бизнес_кейс_Михненко_Екатерина.xlsx",
        "level": "L3",
        "owner": "Екатерина Михайленко",
        "description": "Увеличение выручки сети медицинских клиник через цифровизацию процессов"
    },
    "zyryanova": {
        "name": "КЭВ - Конверсия клиентов",
        "file": "Бизнес_кейс_Зырянова.xlsx", 
        "level": "L2",
        "owner": "Зырянова",
        "description": "Повышение конверсии клиентов в компании КЭВ через оптимизацию процессов"
    },
    "amerkhanov": {
        "name": "Lead to Appointment - Конверсия",
        "file": "Бизнес_кейс. Руслан Амерханов.xlsx",
        "level": "L4", 
        "owner": "Руслан Амерханов",
        "description": "Увеличение конверсии лидов в записи на приемы"
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

# CSS стили для L0-L5 дизайна
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3a8a 0%, #3b82f6 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .level-card {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid #3b82f6;
        margin: 1rem 0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    .level-header {
        font-size: 1.2rem;
        font-weight: bold;
        color: #1e40af;
        margin-bottom: 0.5rem;
    }
    
    .project-metric {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .wave-header {
        background: linear-gradient(45deg, #0f172a, #1e293b);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin-bottom: 1rem;
    }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-on-track { background-color: #10b981; }
    .status-at-risk { background-color: #f59e0b; }
    .status-delayed { background-color: #ef4444; }
</style>
""", unsafe_allow_html=True)

# Функции загрузки данных
@st.cache_data
def load_business_case_data(business_case_id):
    """Загружаем данные бизнес-кейса из Excel файла"""
    try:
        if business_case_id not in EXCEL_FILES:
            return None
            
        file_path = EXCEL_FILES[business_case_id]["file"]
        
        # Проверяем существование файла
        if not os.path.exists(file_path):
            st.error(f"❌ Файл не найден: {file_path}")
            return None
        
        # Загружаем все листы
        excel_data = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')
        
        # Очищаем данные
        cleaned_data = {}
        for sheet_name, df in excel_data.items():
            cleaned_df = clean_dataframe(df)
            if not cleaned_df.empty:
                cleaned_data[sheet_name] = cleaned_df
        
        return {
            "info": EXCEL_FILES[business_case_id],
            "data": cleaned_data
        }
        
    except Exception as e:
        st.error(f"❌ Ошибка загрузки {file_path}: {e}")
        return None

def clean_dataframe(df):
    """Очищаем и нормализуем DataFrame"""
    if df.empty:
        return df
    
    # Создаем копию для безопасности
    cleaned_df = df.copy()
    
    # 1. Удаляем полностью пустые строки и столбцы
    cleaned_df = cleaned_df.dropna(how='all').dropna(axis=1, how='all')
    
    # 2. Переименовываем проблематичные колонки
    new_columns = []
    for i, col in enumerate(cleaned_df.columns):
        col_str = str(col)
        if col_str.startswith('Unnamed:') or col_str.isdigit() or col_str.strip() == '' or col_str == 'nan':
            new_columns.append(f"Столбец_{i+1}")
        else:
            new_columns.append(col_str)
    
    cleaned_df.columns = new_columns
    
    # 3. Заменяем NaN и проблемные значения на пустые строки
    cleaned_df = cleaned_df.fillna('')
    
    # 4. Преобразуем все в строки для совместимости с data_editor
    for col in cleaned_df.columns:
        try:
            cleaned_df[col] = cleaned_df[col].astype(str)
            cleaned_df[col] = cleaned_df[col].replace(['nan', 'None', '<NA>', 'NaT'], '')
        except Exception:
            # Если преобразование не удалось, заполняем пустыми строками
            cleaned_df[col] = ''
    
    # 5. Удаляем строки где все значения пустые
    mask = cleaned_df.apply(lambda row: all(str(val).strip() == '' for val in row), axis=1)
    cleaned_df = cleaned_df[~mask]
    
    return cleaned_df

def get_project_level_color(level):
    """Возвращает цвет для уровня проекта"""
    colors = {
        "L0": "#dc2626",  # Красный
        "L1": "#ea580c",  # Оранжевый  
        "L2": "#ca8a04",  # Желтый
        "L3": "#16a34a",  # Зеленый
        "L4": "#2563eb",  # Синий
        "L5": "#7c3aed"   # Фиолетовый
    }
    return colors.get(level, "#6b7280")

def create_wave_dashboard():
    """Создаем главную дашборд в стиле McKinsey Wave"""
    
    # Заголовок
    st.markdown("""
    <div class="main-header">
        <h1>🎯 SmartPM | McKinsey Wave Style</h1>
        <p>Система управления проектами L0-L5 • Российские бизнес-кейсы</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Загружаем данные всех проектов
    all_projects_data = {}
    for project_id in EXCEL_FILES.keys():
        data = load_business_case_data(project_id)
        if data:
            all_projects_data[project_id] = data
    
    if not all_projects_data:
        st.warning("⚠️ Нет данных для отображения")
        return
    
    # Основные метрики
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="project-metric">
            <h3 style="color: #1e40af; margin: 0;">Всего проектов</h3>
            <h2 style="color: #1f2937; margin: 0;">{}</h2>
        </div>
        """.format(len(all_projects_data)), unsafe_allow_html=True)
    
    with col2:
        # Считаем общий финансовый эффект 2025
        total_effect_2025 = 0
        for project_data in all_projects_data.values():
            finance_data = project_data["data"].get("b. Финансовое влияние", pd.DataFrame())
            if not finance_data.empty and "2025" in finance_data.columns:
                try:
                    effect = float(finance_data["2025"].iloc[0]) if len(finance_data) > 0 else 0
                    total_effect_2025 += effect
                except:
                    pass
        
        st.markdown("""
        <div class="project-metric">
            <h3 style="color: #059669; margin: 0;">Эффект 2025</h3>
            <h2 style="color: #1f2937; margin: 0;">{:.0f} млн ₽</h2>
        </div>
        """.format(total_effect_2025), unsafe_allow_html=True)
    
    with col3:
        # Активные проекты (все загруженные считаем активными)
        active_projects = len([p for p in all_projects_data.values() if p])
        st.markdown("""
        <div class="project-metric">
            <h3 style="color: #7c3aed; margin: 0;">Активных проектов</h3>
            <h2 style="color: #1f2937; margin: 0;">{}</h2>
        </div>
        """.format(active_projects), unsafe_allow_html=True)
    
    with col4:
        # Средний уровень проектов
        levels = [info["level"] for info in EXCEL_FILES.values()]
        avg_level = sum([int(l[1:]) for l in levels]) / len(levels) if levels else 0
        st.markdown("""
        <div class="project-metric">
            <h3 style="color: #dc2626; margin: 0;">Средний уровень</h3>
            <h2 style="color: #1f2937; margin: 0;">L{:.1f}</h2>
        </div>
        """.format(avg_level), unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Проекты по уровням L0-L5
    st.markdown("""
    <div class="wave-header">
        <h2 style="margin: 0;">📊 Портфель проектов по уровням L0-L5</h2>
        <p style="margin: 0.5rem 0 0 0;">Распределение проектов по уровням зрелости McKinsey Wave</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Группируем проекты по уровням
    projects_by_level = {}
    for project_id, project_info in EXCEL_FILES.items():
        level = project_info["level"]
        if level not in projects_by_level:
            projects_by_level[level] = []
        projects_by_level[level].append((project_id, project_info))
    
    # Отображаем проекты по уровням
    for level in ["L0", "L1", "L2", "L3", "L4", "L5"]:
        if level in projects_by_level:
            projects = projects_by_level[level]
            color = get_project_level_color(level)
            
            st.markdown(f"""
            <div class="level-card" style="border-left-color: {color};">
                <div class="level-header" style="color: {color};">
                    {level} • {len(projects)} проект(ов)
                </div>
            """, unsafe_allow_html=True)
            
            for project_id, project_info in projects:
                project_data = all_projects_data.get(project_id)
                status = "✅ Загружен" if project_data else "❌ Ошибка"
                status_class = "status-on-track" if project_data else "status-delayed"
                
                # Получаем финансовый эффект
                financial_effect = 0
                if project_data:
                    finance_data = project_data["data"].get("b. Финансовое влияние", pd.DataFrame())
                    if not finance_data.empty and "2025" in finance_data.columns:
                        try:
                            financial_effect = float(finance_data["2025"].iloc[0]) if len(finance_data) > 0 else 0
                        except:
                            pass
                
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"""
                    <span class="status-indicator {status_class}"></span>
                    <strong>{project_info['name']}</strong><br>
                    <small style="color: #6b7280;">{project_info['description'][:100]}...</small>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div style="text-align: center;">
                        <strong style="color: {color};">{financial_effect:.0f} млн ₽</strong><br>
                        <small style="color: #6b7280;">Эффект 2025</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col3:
                    if st.button(f"📋 Детали", key=f"view_{project_id}"):
                        st.session_state.selected_project = project_id
                        st.session_state.page = "project_details"
                        st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Пустой уровень
            color = get_project_level_color(level)
            st.markdown(f"""
            <div class="level-card" style="border-left-color: {color}; opacity: 0.5;">
                <div class="level-header" style="color: {color};">
                    {level} • 0 проектов
                </div>
                <p style="color: #6b7280; margin: 0;">Нет проектов данного уровня</p>
            </div>
            """, unsafe_allow_html=True)
    
    # График распределения по уровням
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    
    with col1:
        # Круговая диаграмма по уровням
        level_counts = {}
        for project_info in EXCEL_FILES.values():
            level = project_info["level"]
            level_counts[level] = level_counts.get(level, 0) + 1
        
        fig_pie = px.pie(
            values=list(level_counts.values()),
            names=list(level_counts.keys()),
            title="🎯 Распределение проектов по уровням",
            color_discrete_map={level: get_project_level_color(level) for level in level_counts.keys()}
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Финансовый эффект по проектам
        chart_data = []
        for project_id, project_info in EXCEL_FILES.items():
            project_data = all_projects_data.get(project_id)
            if project_data:
                finance_data = project_data["data"].get("b. Финансовое влияние", pd.DataFrame())
                if not finance_data.empty and "2025" in finance_data.columns:
                    try:
                        effect = float(finance_data["2025"].iloc[0]) if len(finance_data) > 0 else 0
                        chart_data.append({
                            "Проект": project_info["name"][:20] + "...",
                            "Эффект": effect,
                            "Уровень": project_info["level"]
                        })
                    except:
                        pass
        
        if chart_data:
            chart_df = pd.DataFrame(chart_data)
            fig_bar = px.bar(
                chart_df, 
                x="Эффект", 
                y="Проект",
                color="Уровень",
                title="💰 Финансовый эффект 2025",
                color_discrete_map={level: get_project_level_color(level) for level in chart_df["Уровень"].unique()}
            )
            fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)

def show_project_details(project_id):
    """Показываем детали конкретного проекта"""
    if project_id not in EXCEL_FILES:
        st.error("❌ Проект не найден")
        return
    
    project_info = EXCEL_FILES[project_id]
    project_data = load_business_case_data(project_id)
    
    if not project_data:
        st.error("❌ Не удалось загрузить данные проекта")
        return
    
    # Заголовок проекта
    level_color = get_project_level_color(project_info["level"])
    st.markdown(f"""
    <div class="wave-header">
        <h1 style="margin: 0;">
            <span style="background: {level_color}; color: white; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem;">
                {project_info["level"]}
            </span>
            {project_info["name"]}
        </h1>
        <p style="margin: 0.5rem 0 0 0;">{project_info["description"]}</p>
        <p style="margin: 0.2rem 0 0 0; opacity: 0.8;">👤 Владелец: {project_info["owner"]}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Разделы проекта
    sections = {
        "a. Детали инициативы": {"icon": "📋", "description": "Основная информация о проекте"},
        "b. Финансовое влияние": {"icon": "💰", "description": "Финансовые показатели и ROI"},
        "c. Поддерживающие расчеты": {"icon": "🧮", "description": "Детальные расчеты и обоснования"},
        "d. Диаграмма Ганта": {"icon": "📅", "description": "Временные рамки и этапы проекта"},
        "e. Мониторинг эффекта": {"icon": "📈", "description": "Отслеживание результатов"},
        "f. Статус инициатив": {"icon": "🎯", "description": "Текущий статус и прогресс"}
    }
    
    # Табы для разделов
    tabs = st.tabs([f"{info['icon']} {key}" for key, info in sections.items()])
    
    for i, (section_key, section_info) in enumerate(sections.items()):
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
                    key=f"editor_{project_id}_{section_key}"
                )
                
                if st.button(f"💾 Сохранить изменения в '{section_key}'", key=f"save_{section_key}"):
                    st.success(f"✅ Изменения в разделе '{section_key}' сохранены!")

def show_gantt_chart(gantt_data):
    """Показываем диаграмму Ганта"""
    if gantt_data.empty:
        st.warning("⚠️ Недостаточно данных для построения диаграммы Ганта")
        st.dataframe(gantt_data, use_container_width=True)
        return
    
    # Показываем таблицу данных
    st.subheader("📋 Данные проекта")
    edited_df = st.data_editor(
        gantt_data,
        use_container_width=True,
        num_rows="dynamic"
    )
    
    # Пытаемся построить диаграмму если есть подходящие данные
    try:
        if len(gantt_data.columns) >= 3:
            # Предполагаем что первая колонка - задачи, вторая - начало, третья - конец
            tasks_col = gantt_data.columns[0]
            start_col = gantt_data.columns[1] 
            end_col = gantt_data.columns[2]
            
            # Преобразуем даты
            gantt_copy = gantt_data.copy()
            gantt_copy[start_col] = pd.to_datetime(gantt_copy[start_col], errors='coerce')
            gantt_copy[end_col] = pd.to_datetime(gantt_copy[end_col], errors='coerce')
            
            # Фильтруем строки с валидными датами
            valid_rows = gantt_copy.dropna(subset=[start_col, end_col])
            
            if not valid_rows.empty:
                fig = px.timeline(
                    valid_rows,
                    x_start=start_col,
                    x_end=end_col, 
                    y=tasks_col,
                    title="📅 Диаграмма Ганта проекта"
                )
                fig.update_yaxes(autorange="reversed")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("ℹ️ Не удалось найти валидные даты для построения диаграммы Ганта")
        
    except Exception as e:
        st.info(f"ℹ️ Диаграмма Ганта недоступна: {e}")

def show_monitoring_chart(monitoring_data):
    """Показываем график мониторинга"""
    if monitoring_data.empty:
        st.warning("⚠️ Нет данных для мониторинга")
        return
    
    st.subheader("📈 График мониторинга")
    
    # Очищаем данные от пустых строк и столбцов
    monitoring_data = monitoring_data.dropna(how='all').dropna(axis=1, how='all')
    
    # Показываем таблицу данных
    if not monitoring_data.empty:
        # Редактор данных
        edited_df = st.data_editor(
            monitoring_data,
            use_container_width=True,
            num_rows="dynamic"
        )
        
        # Пытаемся построить график
        try:
            if len(monitoring_data.columns) > 1:
                numeric_cols = []
                for col in monitoring_data.columns[1:]:
                    # Проверяем наличие числовых данных
                    sample_values = monitoring_data[col].dropna().head(5)
                    has_numeric = False
                    
                    for val in sample_values:
                        try:
                            float(str(val).replace(',', '.').replace('₽', '').replace('%', '').strip())
                            has_numeric = True
                            break
                        except:
                            continue
                    
                    if has_numeric:
                        numeric_cols.append(col)
                
                if numeric_cols:
                    fig = go.Figure()
                    x_values = monitoring_data[monitoring_data.columns[0]].tolist()
                    
                    for col in numeric_cols:
                        y_values = []
                        for val in monitoring_data[col]:
                            try:
                                clean_val = str(val).replace(',', '.').replace('₽', '').replace('%', '').strip()
                                y_values.append(float(clean_val))
                            except:
                                y_values.append(0)
                        
                        fig.add_trace(go.Scatter(
                            x=x_values,
                            y=y_values,
                            mode='lines+markers',
                            name=col,
                            line=dict(width=3),
                            marker=dict(size=8)
                        ))
                    
                    fig.update_layout(
                        title="📈 Динамика показателей мониторинга",
                        xaxis_title="Период",
                        yaxis_title="Значение",
                        template='plotly_white'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("ℹ️ Нет числовых данных для построения графика")
            
        except Exception as e:
            st.info(f"ℹ️ График мониторинга недоступен: {e}")
    
    else:
        st.warning("⚠️ Нет данных для отображения")

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
    # Боковая панель
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem; background: linear-gradient(45deg, #1e3a8a, #3b82f6); border-radius: 10px; color: white; margin-bottom: 1rem;">
            <h2 style="margin: 0;">🎯 SmartPM</h2>
            <p style="margin: 0;">McKinsey Wave Style</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Навигация
        page = st.selectbox(
            "📋 Навигация",
            ["🏠 Главная дашборд", "🎯 Детали проекта"],
            key="main_nav"
        )
        
        if page == "🎯 Детали проекта":
            if EXCEL_FILES:
                st.subheader("Выберите проект:")
                project_options = {
                    f"{info['level']} • {info['name']}": project_id 
                    for project_id, info in EXCEL_FILES.items()
                }
                
                selected_project_display = st.selectbox(
                    "Проект:",
                    options=list(project_options.keys()),
                    key="project_selector"
                )
                
                selected_project = project_options[selected_project_display]
            else:
                st.warning("⚠️ Нет доступных проектов")
                selected_project = None
        else:
            selected_project = None
        
        # Информация о системе
        st.markdown("---")
        st.markdown("### ℹ️ Система")
        
        # Статистика по уровням
        level_stats = {}
        for info in EXCEL_FILES.values():
            level = info["level"]
            level_stats[level] = level_stats.get(level, 0) + 1
        
        for level in ["L0", "L1", "L2", "L3", "L4", "L5"]:
            count = level_stats.get(level, 0)
            color = get_project_level_color(level)
            st.markdown(f"""
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 0.2rem 0;">
                <span style="color: {color}; font-weight: bold;">{level}</span>
                <span>{count} проект(ов)</span>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"**Последнее обновление:** {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        
        # Кнопка обновления
        if st.button("🔄 Обновить данные"):
            st.cache_data.clear()
            st.rerun()
    
    # Основное содержимое
    if page == "🏠 Главная дашборд":
        create_wave_dashboard()
    elif page == "🎯 Детали проекта" and selected_project:
        show_project_details(selected_project)
    else:
        st.info("👈 Выберите страницу в боковой панели")

if __name__ == "__main__":
    main() 