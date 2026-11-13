import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 1. Настройка стиля визуализации для академического качества
sns.set_theme(style="whitegrid", context="talk")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans'] # Для корректного отображения

# 2. Загрузка и предварительная обработка данных
file_path = '/content/manifest.csv'
print(f"Загрузка данных из {file_path}...")
df = pd.read_csv(file_path)

# Преобразуем ключевые метрики в числовой формат, обрабатывая возможные ошибки парсинга
df['qubits'] = pd.to_numeric(df['qubits'], errors='coerce')
df['local_task_score'] = pd.to_numeric(df['local_task_score'], errors='coerce')
df['dqi_expected_cost'] = pd.to_numeric(df['dqi_expected_cost'], errors='coerce')

# Создаем унифицированную метрику "стоимость" (cost). 
# Для задачи dqi приоритетнее dqi_expected_cost, для остальных - local_task_score
df['effective_cost'] = df['dqi_expected_cost'].fillna(df['local_task_score'])

# Удаляем строки, где отсутствуют критически важные данные для анализа
df_clean = df.dropna(subset=['qubits', 'effective_cost', 'task']).copy()
print(f"Очищено данных: {len(df_clean)} строк из {len(df)}")

# 3. Алгоритм поиска Парето-фронта
def find_pareto_frontier(group):
    """
    Находит Парето-оптимальные точки в группе данных.
    Мы минимизируем обе оси: X (qubits) и Y (effective_cost).
    """
    # Сортируем по X возрастанию, затем по Y возрастанию
    sorted_group = group.sort_values(by=['qubits', 'effective_cost'], ascending=[True, True]).copy()
    
    pareto_mask = []
    min_cost = np.inf
    
    for _, row in sorted_group.iterrows():
        # Если текущая стоимость строго меньше минимальной встреченной при движении вправо по X,
        # значит, эта точка не доминируется ни одной предыдущей (у которой X меньше или равен).
        if row['effective_cost'] < min_cost:
            pareto_mask.append(True)
            min_cost = row['effective_cost']
        else:
            pareto_mask.append(False)
            
    sorted_group['is_pareto'] = pareto_mask
    return sorted_group

# Применяем алгоритм независимо для каждой задачи (task), так как сравнивать их напрямую некорректно
df_analyzed = df_clean.groupby('task', group_keys=False).apply(find_pareto_frontier)

# 4. Визуализация Парето-фронта
# Разделяем на подграфики по типу задачи для сохранения масштаба
g = sns.relplot(
    data=df_analyzed,
    x='qubits',
    y='effective_cost',
    hue='is_pareto',
    style='is_pareto',
    col='task',
    col_wrap=2, # По 2 графика в ряд
    height=5,
    aspect=1.2,
    palette={True: '#d62728', False: '#1f77b4'}, # Красный для Парето, синий для остальных
    markers={True: 'D', False: 'o'}, # Ромб для Парето, круг для остальных
    sizes={True: 150, False: 40},
    alpha=0.7
)

# Настройка осей и аннотаций для каждого подграфика
for ax in g.axes.flat:
    # Логарифмическая шкала по Y, так как разброс стоимости огромен
    ax.set_yscale('log')
    ax.set_xlabel('Количество кубитов (Qubits) ↓')
    ax.set_ylabel('Стоимость / Ошибка (Log Scale) ↓')
    ax.set_title(ax.get_title().replace('task = ', ''), fontsize=14, fontweight='bold')
    
    # Добавляем аннотации только для Парето-оптимальных точек, чтобы не перегружать график
    pareto_points = df_analyzed[(df_analyzed['is_pareto']) & (df_analyzed['task'] == ax.get_title().replace('task = ', ''))]
    
    for _, row in pareto_points.iterrows():
        # Берем только первые 15 символов имени автора или названия, чтобы текст влезал
        label = row['author'][:15] + '...' if len(str(row['author'])) > 15 else str(row['author'])
        ax.annotate(
            label,
            (row['qubits'], row['effective_cost']),
            textcoords="offset points",
            xytext=(8, 5),
            fontsize=9,
            color='#d62728',
            fontweight='bold',
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#d62728", alpha=0.8)
        )

# Общий заголовок
g.figure.suptitle('Парето-фронт эффективности квантовых схем\n(Минимизация кубитов и стоимости)', 
                  y=1.02, fontsize=18, fontweight='bold')

plt.tight_layout()
plt.show()

# 5. Вывод таблицы с лучшими (Парето-оптимальными) решениями для детального анализа
print("\n" + "="*80)
print("ТОП ПАРето-ОПТИМАЛЬНЫХ РЕШЕНИЙ ПО ЗАДАЧАМ")
print("="*80)
display_cols = ['task', 'author', 'notebook_title', 'qubits', 'effective_cost', 'change_summary']
pareto_df = df_analyzed[df_analyzed['is_pareto']][display_cols].sort_values(by=['task', 'qubits'])
pd.set_option('display.max_colwidth', 100)
display(pareto_df.reset_index(drop=True))