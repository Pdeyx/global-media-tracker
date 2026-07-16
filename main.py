import sqlite3
import feedparser
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from groq import Groq
import os
from dotenv import load_dotenv  # <--- ДОБАВИТЬ ЭТО

load_dotenv()  # <--- И ДОБАВИТЬ ЭТО. Эта команда заставит Python прочитать файл .env

# Дальше твой код как обычно:
analyzer = SentimentIntensityAnalyzer()
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Наш обновленный и расширенный список источников
news_feeds = {
    "США (CNN)": "http://rss.cnn.com/rss/edition_world.rss",
    "США (Fox)": "http://feeds.foxnews.com/foxnews/world",
    "Европа (BBC)": "http://newsrss.bbc.co.uk/rss/newsonline_world_edition/front_page/rss.xml",
    "Европа (DW)": "https://rss.dw.com/rdf/rss-en-world",
    "Россия (RT)": "https://www.rt.com/rss/news/",
    "Азия (Al Jazeera)": "https://www.aljazeera.com/xml/rss/all.xml"
}

def init_db():
    conn = sqlite3.connect("news_tracker.db")
    cursor = conn.cursor()
    
    # Добавили новую колонку: ai_explanation
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            title TEXT,
            link TEXT UNIQUE,
            pub_date TEXT,
            fetched_at TEXT,
            neg REAL,
            neu REAL,
            pos REAL,
            compound REAL,
            ai_explanation TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_ai_insight(title, source):
    """Отправляет заголовок нейросети и возвращает текстовый анализ"""
    prompt = f"Проанализируй этот новостной заголовок от издания {source}: '{title}'. Напиши ровно 2 предложения на русском языке: первое - какой эмоциональный тон задает заголовок, второе - есть ли тут скрытая предвзятость, манипуляция или это сухой факт."
    
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "Ты профессиональный медиа-аналитик. Отвечай строго по делу, без приветствий."},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile", # Используем мощную модель Llama 3
            temperature=0.3 # Низкая температура делает ответы ИИ более точными и менее фантазийными
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Ошибка: {e}"

def collect_and_analyze_news():
    print("\n--- ЗАПУСК ГЛУБОКОГО ИИ-АНАЛИЗА НОВОСТЕЙ ---\n")
    
    conn = sqlite3.connect("news_tracker.db")
    cursor = conn.cursor()
    new_articles_counter = 0
    
    for source_name, url in news_feeds.items():
        print(f"📡 Сбор и анализ: {source_name}...")
        
        feed = feedparser.parse(url)
        # Берем по 2 самые свежие новости с каждого ресурса, чтобы не ждать слишком долго
        latest_posts = feed.entries[:2] 
        
        for post in latest_posts:
            title = post.title
            link = post.link
            pub_date = getattr(post, 'published', 'Дата не указана')
            fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Получаем цифры для графика (от VADER)
            sentiment = analyzer.polarity_scores(title)
            compound = sentiment['compound']
            
            # --- НОВАЯ МАГИЯ: Получаем текстовый анализ от Groq ---
            ai_text = get_ai_insight(title, source_name)
            
            try:
                cursor.execute("""
                    INSERT INTO articles 
                    (source, title, link, pub_date, fetched_at, neg, neu, pos, compound, ai_explanation)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (source_name, title, link, pub_date, fetched_at, 
                      sentiment['neg'], sentiment['neu'], sentiment['pos'], compound, ai_text))
                
                new_articles_counter += 1
                
                print(f"  📌 {title[:50]}...")
                print(f"  🤖 Анализ: {ai_text}\n")
                
            except sqlite3.IntegrityError:
                pass # Пропускаем дубликаты
                
    conn.commit()
    conn.close()
    
    print(f"--- СБОР ЗАВЕРШЕН. Добавлено новостей: {new_articles_counter} ---")

if __name__ == "__main__":
    init_db() 
    collect_and_analyze_news()