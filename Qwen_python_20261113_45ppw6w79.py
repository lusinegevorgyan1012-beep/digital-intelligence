import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Загрузка данных
# Примечание: если вы загрузили файл через панель слева в Colab, путь может начинаться с /content/
file_path = '/Messages_МосУ_МВД_России_имени_В_Я_Кикотя.csv'

try:
    df = pd.read_csv(file_path, sep=';')
except FileNotFoundError:
    # Фоллбэк, если файл лежит в стандартной папке Colab
    file_path = '/content/Messages_МосУ_МВД_России_имени_В_Я_Кикотя.csv'
    df = pd.read_csv(file_path, sep=';')

print(f"✅ Файл успешно загружен. Всего строк: {len(df)}")

# 2. Предварительная очистка данных
# Оставляем только основные текстовые посты (отфильтровываем медиа-вложения альбомов)
df = df[df['message'] != 'MediaMessage'].copy()
print(f"📊 После фильтрации медиа-вложений осталось {len(df)} основных постов.")

# Преобразуем столбец с датой в формат datetime
df['date'] = pd.to_datetime(df['date'])

# Переводим время из UTC в Московское время (Europe/Moscow)
df['date_msk'] = df['date'].dt.tz_convert('Europe/Moscow')

# Извлекаем час и день недели
df['hour'] = df['date_msk'].dt.hour
df['day_of_week_num'] = df['date_msk'].dt.dayofweek  # 0 = Понедельник, 6 = Воскресенье

# Маппинг дней недели на русский язык для графиков
days_map = {0: 'Понедельник', 1: 'Вторник', 2: 'Среда', 3: 'Четверг',
            4: 'Пятница', 5: 'Суббота', 6: 'Воскресенье'}
df['day_name'] = df['day_of_week_num'].map(days_map)

# Приводим просмотры к числовому формату (на случай пустых значений)
df['views'] = pd.to_numeric(df['views'], errors='coerce').fillna(0)

# 3. Анализ и расчет средних значений
# Группируем по дню недели и часу
pivot_views = df.groupby(['day_name', 'hour'])['views'].mean().unstack()

# Задаем правильный порядок дней недели для тепловой карты
days_order = ['Понедельник', 'Вторник', 'Среда', 'Четверг', 'Пятница', 'Суббота', 'Воскресенье']
pivot_views = pivot_views.reindex(days_order)

# 4. Визуализация
plt.rcParams['font.family'] = 'DejaVu Sans' # Поддержка кириллицы (в Colab обычно работает, но на всякий случай)

fig = plt.figure(figsize=(16, 12))

# График 1: Тепловая карта (Heatmap)
plt.subplot(2, 1, 1)
sns.heatmap(pivot_views, cmap='YlGnBu', annot=False, fmt=".0f", cbar_kws={'label': 'Средние просмотры'}, linewidths=.5)
plt.title('🔥 Тепловая карта: Средние просмотры по Дням недели и Часам (МСК)', fontsize=14, pad=10)
plt.xlabel('Час дня (МСК)', fontsize=12)
plt.ylabel('День недели', fontsize=12)
plt.xticks(rotation=0)
plt.yticks(rotation=0)

# График 2: Средние просмотры по часам
plt.subplot(2, 2, 3)
hourly_views = df.groupby('hour')['views'].mean()
plt.bar(hourly_views.index, hourly_views.values, color='skyblue', edgecolor='black')
plt.title('📈 Средние просмотры по часам', fontsize=12)
plt.xlabel('Час (МСК)')
plt.ylabel('Средние просмотры')
plt.xticks(range(24))
plt.grid(axis='y', linestyle='--', alpha=0.7)

# График 3: Средние просмотры по дням недели
plt.subplot(2, 2, 4)
daily_views = df.groupby(['day_name', 'day_of_week_num'])['views'].mean().reset_index()
daily_views = daily_views.sort_values('day_of_week_num')
plt.bar(daily_views['day_name'], daily_views['views'], color='lightgreen', edgecolor='black')
plt.title('📅 Средние просмотры по дням недели', fontsize=12)
plt.ylabel('Средние просмотры')
plt.xticks(rotation=45)
plt.grid(axis='y', linestyle='--', alpha=0.7)

plt.tight_layout()
plt.show()

# 5. Вывод текстовых рекомендаций
print("\n" + "="*50)
print("🏆 АНАЛИЗ ЛУЧШЕГО ВРЕМЕНИ ДЛЯ ПУБЛИКАЦИЙ (МСК)")
print("="*50)

# Топ-3 часа
top_hours = hourly_views.sort_values(ascending=False).head(3)
print("\n⏰ Топ-3 лучших ЧАСОВ для публикаций:")
for hour, val in top_hours.items():
    print(f"   • {hour:02d}:00 - {int(val)} просмотров в среднем")

# Топ-3 дня
top_days = daily_views.sort_values('views', ascending=False).head(3)
print("\n📆 Топ-3 лучших ДНЕЙ НЕДЕЛИ для публикаций:")
for _, row in top_days.iterrows():
    print(f"   • {row['day_name']} - {int(row['views'])} просмотров в среднем")

# Общий топ слотов (День + Час)
best_slots = df.groupby(['day_name', 'hour'])['views'].mean().sort_values(ascending=False).head(3)
print("\n🎯 Топ-3 идеальных СЛОТОВ (День + Час):")
for (day, hour), val in best_slots.items():
    print(f"   • {day}, {hour:02d}:00 - {int(val)} просмотров")