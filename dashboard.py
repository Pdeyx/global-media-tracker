import sqlite3
import matplotlib.pyplot as plt

def plot_average_sentiment():
    print("📊 Подключаемся к базе данных для анализа...")
    
    # 1. Подключаемся к базе
    conn = sqlite3.connect("news_tracker.db")
    cursor = conn.cursor()
    
    # 2. Делаем SQL-запрос: считаем СРЕДНЕЕ значение compound для каждого СМИ
    cursor.execute("""
        SELECT source, AVG(compound) 
        FROM articles 
        GROUP BY source
    """)
    
    data = cursor.fetchall()
    conn.close()
    
    if not data:
        print("База данных пуста! Сначала запусти main.py")
        return

    # 3. Разделяем данные для графика (названия СМИ и их средний балл)
    sources = [row[0] for row in data]
    avg_scores = [row[1] for row in data]
    
    # 4. Рисуем график
    plt.figure(figsize=(10, 6)) # Размер окна
    
    # Назначаем цвета: если средний балл меньше 0 - красный, если больше - зеленый
    colors = ['red' if score < 0 else 'green' for score in avg_scores]
    
    # Строим столбчатую диаграмму
    bars = plt.bar(sources, avg_scores, color=colors)
    
    # Наводим красоту: заголовки и линии
    plt.title("Средняя эмоциональная тональность мировых СМИ (AI Анализ)", fontsize=14)
    plt.ylabel("Уровень тональности (от -1.0 до 1.0)", fontsize=12)
    plt.axhline(0, color='black', linewidth=1) # Черная линия на нуле
    
    # Добавляем цифры над столбцами
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + (0.02 if yval > 0 else -0.05), 
                 round(yval, 3), ha='center', va='bottom' if yval > 0 else 'top', fontweight='bold')
    
    print("📈 График успешно сгенерирован! Открываю окно...")
    plt.show()

if __name__ == "__main__":
    plot_average_sentiment()