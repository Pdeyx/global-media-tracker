import streamlit as st
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# 1. Базовые настройки страницы
st.set_page_config(page_title="Global Media Tracker | Portfolio", page_icon="🌍", layout="wide")

# 2. ИНЪЕКЦИЯ CSS (Прячем интерфейс Streamlit и делаем дизайнерский вид)
st.markdown("""
    <style>
    /* Прячем стандартное верхнее меню и футер Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Стилизуем карточки метрик */
    div[data-testid="metric-container"] {
        background-color: #1E1E1E;
        border: 1px solid #333;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Стилизуем заголовок */
    .main-title {
        font-size: 3rem;
        font-weight: 800;
        background: -webkit-linear-gradient(45deg, #4b6cb7, #182848);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .sub-title {
        color: #A0A0A0;
        font-size: 1.2rem;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

def load_data():
    conn = sqlite3.connect("news_tracker.db")
    df = pd.read_sql_query("SELECT * FROM articles ORDER BY fetched_at DESC", conn)
    conn.close()
    return df

df = load_data()

# --- БЛОК 1: HERO SECTION (Главный экран) ---
st.markdown('<p class="main-title">Global Media Bias Tracker</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Автоматизированная система мониторинга предвзятости СМИ с использованием Llama 3 и NLP-анализа.</p>', unsafe_allow_html=True)

# --- БЛОК 2: О ПРОЕКТЕ И ОБО МНЕ (Презентация для комиссии) ---
with st.container():
    col_about, col_me = st.columns([2, 1])
    
    with col_about:
        st.subheader("💡 О проекте")
        st.write("""
        Этот аналитический инструмент в реальном времени собирает заголовки из крупнейших мировых изданий (CNN, BBC, RT, Al Jazeera). 
        
        **Как это работает:**
        1. **Data Engineering:** Python-скрипт парсит RSS-ленты и сохраняет данные в базу SQLite.
        2. **NLP Analysis:** Алгоритм VADER вычисляет статистический индекс тональности (от -1.0 до 1.0).
        3. **Generative AI:** Нейросеть Llama 3 читает каждый заголовок и выявляет скрытые манипуляции, пропаганду или эмоциональный окрас.
        """)
        
    with col_me:
        st.subheader("👨‍💻 Разработчик")
        st.info("""
        **Антон П.** *Software Engineering Student* Увлекаюсь веб-разработкой, анализом данных и искусственным интеллектом. Создаю проекты на стыке технологий и социальных процессов.
        
        🔗 [Мой GitHub](#) | ✉️ [Email](#)
        """)

st.divider()

if df.empty:
    st.error("База данных пуста. Необходимо запустить pipeline сбора данных (main.py).")
else:
    # --- БЛОК 3: МЕТРИКИ ---
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Обработано новостей", len(df))
    with col2:
        avg_all = round(df['compound'].mean(), 3)
        st.metric("Глобальный индекс (VADER)", avg_all)
    with col3:
        st.metric("Активных источников", df['source'].nunique())
        
    st.write("") # Отступ
    
    # --- БЛОК 4: ВИЗУАЛИЗАЦИЯ (График) ---
    st.subheader("📊 Анализ эмоционального фона по регионам")
    avg_sentiment = df.groupby("source")["compound"].mean().sort_values()
    
    fig, ax = plt.subplots(figsize=(10, 3)) 
    fig.patch.set_alpha(0.0) 
    ax.patch.set_alpha(0.0)
    
    colors = ['#ff4b4b' if x < 0 else '#21c354' for x in avg_sentiment.values]
    ax.bar(avg_sentiment.index, avg_sentiment.values, color=colors)
    ax.axhline(0, color='gray', linewidth=1, linestyle='--')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.tick_params(colors='gray')
    
    st.pyplot(fig)
    
    st.divider()
    
    # --- БЛОК 5: ЛЕНТА ИИ-АНАЛИЗА ---
    st.subheader("📡 Live Feed: AI Insight")
    
    for index, row in df.head(15).iterrows():
        with st.expander(f"{row['source']} | {row['title']}"):
            c1, c2 = st.columns([1, 3])
            
            with c1:
                st.caption(f"🕒 {row['fetched_at']}")
                st.markdown(f"[🔗 Источник]({row['link']})")
                
                # Визуальная оценка
                score = row['compound']
                if score > 0.05:
                    st.success(f"VADER: {round(score, 2)}")
                elif score < -0.05:
                    st.error(f"VADER: {round(score, 2)}")
                else:
                    st.info(f"VADER: {round(score, 2)}")
                    
            with c2:
                st.write("**Заключение нейросети:**")
                st.write(row['ai_explanation'])