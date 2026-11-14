# Устанавливаем необходимые библиотеки (на случай, если их нет в среде Colab)
!pip install beautifulsoup4 pandas lxml -q

import pandas as pd
from bs4 import BeautifulSoup
import re

# ШАГ 1: Загрузка HTML-кода из локального файла
file_path = '/content/messages.html'
with open(file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

# Инициализируем парсер BeautifulSoup (аналог read_html() в R)
soup = BeautifulSoup(html_content, 'lxml')

# ШАГ 2: Извлечение данных с помощью CSS-селекторов
# Находим все контейнеры с сообщениями
messages_html = soup.find_all('div', class_='message')

data = []

for msg in messages_html:
    # Извлекаем автора (используем CSS-селектор по классу)
    author_tag = msg.select_one('.from_name')
    author = author_tag.get_text(strip=True) if author_tag else 'Неизвестно'
    
    # Извлекаем дату
    date_tag = msg.select_one('.date')
    date = date_tag.get_text(strip=True) if date_tag else ''
    
    # Извлекаем текст сообщения
    text_tag = msg.select_one('.text')
    text = text_tag.get_text(strip=True) if text_tag else ''
    
    # Проверяем, является ли сообщение пересланным (иллюзия контроля над источником)
    forwarded_tag = msg.select_one('.forwarded')
    is_forwarded = True if forwarded_tag else False
    
    # Фильтруем пустые сообщения (например, только с реакциями или медиа)
    if text:
        data.append({
            'Date': date,
            'Author': author,
            'Is_Forwarded': is_forwarded,
            'Text': text
        })

# ШАГ 3: Создание таблицы (аналог data.frame() в R)
df = pd.DataFrame(data)

# ШАГ 4: Первичная очистка данных (Data Wrangling)
# Удаляем лишние пробелы и переносы строк
df['Text'] = df['Text'].apply(lambda x: re.sub(r'\s+', ' ', x).strip())

# Отображаем первые 10 строк для проверки
print(f"Успешно извлечено {len(df)} сообщений.")
display(df.head(10))

# ШАГ 5: Сохранение в CSV (аналог write_csv() в R)
df.to_csv('/content/parsed_telegram_channel.csv', index=False, encoding='utf-8-sig')
print("Данные успешно сохранены в /content/parsed_telegram_channel.csv")