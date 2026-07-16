from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import feedparser
import urllib.parse
import os
from datetime import datetime
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from groq import Groq

app = FastAPI(title="Global Media Tracker API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Инициализируем нейросети
analyzer = SentimentIntensityAnalyzer()
groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def get_db_connection():
    conn = sqlite3.connect("news_tracker.db")
    conn.row_factory = sqlite3.Row
    return conn

# МАРШРУТ 1: Отдает сохраненные новости при загрузке страницы
@app.get("/api/news")
def get_news():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM articles ORDER BY fetched_at DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# МАРШРУТ 2: ЖИВОЙ ПОИСК ПО GOOGLE NEWS (Новая магия!)
@app.get("/api/search")
def live_search(q: str):
    # Кодируем запрос (например, превращаем пробелы в %20)
    query = urllib.parse.quote(q)
    
    # Ищем по мировым новостям (на английском, чтобы VADER работал точнее)
    rss_url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    
    feed = feedparser.parse(rss_url)
    
    # Берем топ-3 самых свежих новости, чтобы ИИ не заставил нас ждать полминуты
    top_articles = feed.entries[:3] 
    
    results = []
    for post in top_articles:
        # Google News часто склеивает заголовок и источник: "Заголовок - CNN"
        full_title = post.title
        source = "Google News"
        if " - " in full_title:
            parts = full_title.split(" - ")
            source = parts[-1] # Название СМИ
            title = " - ".join(parts[:-1]) # Сам заголовок
        else:
            title = full_title
            
        link = post.link
        fetched_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. Считаем статистику VADER
        sentiment = analyzer.polarity_scores(title)
        compound = sentiment['compound']
        
        # 2. Запрашиваем смысловой анализ у Llama 3
        prompt = f"Проанализируй новостной заголовок: '{title}'. Напиши ровно 2 предложения на русском языке: первое - про эмоциональный тон, второе - есть ли тут скрытая предвзятость или манипуляция."
        
        try:
            response = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Ты суровый медиа-аналитик. Отвечай строго по делу, без приветствий."},
                    {"role": "user", "content": prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3
            )
            ai_text = response.choices[0].message.content.strip()
        except Exception as e:
            ai_text = f"Ошибка ИИ: {e}"
            
        # Упаковываем результат
        results.append({
            "source": source,
            "title": title,
            "link": link,
            "fetched_at": fetched_at,
            "compound": compound,
            "ai_explanation": ai_text
        })
        
    return results