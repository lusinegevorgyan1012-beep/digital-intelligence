# ==========================================================
# ШАГ 1: Установка и загрузка библиотек (методичка, 04/ШАГ 1)
# ==========================================================
install.packages(c("rvest", "dplyr", "stringr", "ggplot2", "tidyr", "lubridate"), quiet = TRUE)

library(rvest)
library(dplyr)
library(stringr)
library(ggplot2)
library(tidyr)
library(lubridate)

# ==========================================================
# ШАГ 2: Чтение HTML-кода страницы (методичка, 04/ШАГ 2)
# ==========================================================
file_path <- "/content/messages.html"

if (!file.exists(file_path)) {
  stop("Файл не найден! Загрузите messages.html в папку /content/ в Google Colab.")
}

# read_html() — функция из rvest, как в методичке
html_doc <- read_html(file_path, encoding = "UTF-8")
cat("Файл успешно загружен.\n")

# ==========================================================
# ШАГ 3: Извлечение элементов через CSS-селекторы (методичка, 04/ШАГ 3)
# ==========================================================
# Каждый пост — это div с классом "message"
# CSS-селектор: div.message (аналог a.announce_link из методички)
message_nodes <- html_doc %>% html_elements("div.message")

cat("Найдено узлов сообщений:", length(message_nodes), "\n")

# Создаём пустую таблицу (методичка, 04/ШАГ 4 — data.frame())
df <- data.frame(
  date = character(),
  text = character(),
  total_reactions = numeric(),
  word_count = integer(),
  category = character(),
  is_forwarded = logical(),
  stringsAsFactors = FALSE
)

# Цикл по всем сообщениям (методичка, 04/ШАГ 5 — цикл for)
for (node in message_nodes) {
  
  # --- 1. ДАТА ---
  # CSS-селектор: div.date (аналог .announce_date из методички)
  date_node <- node %>% html_element("div.date")
  date_str <- if (!is.na(date_node)) html_text(date_node, trim = TRUE) else NA
  if (is.na(date_str) || nchar(date_str) < 5) next  # пропускаем узлы без даты
  
  # --- 2. ТЕКСТ ---
  # CSS-селектор: div.text (аналог html_text() из методички)
  text_node <- node %>% html_element("div.text")
  text_content <- if (!is.na(text_node)) html_text(text_node, trim = TRUE) else NA
  if (is.na(text_content) || nchar(text_content) < 10) next
  
  # --- 3. РЕАКЦИИ ---
  # В HTML-экспорте Telegram реакции лежат в div.reactions
  # Внутри — span или div с эмодзи и числом
  reactions_nodes <- node %>% html_elements("div.reactions div, div.reactions span")
  total_reactions <- 0
  
  if (length(reactions_nodes) > 0) {
    for (r in reactions_nodes) {
      r_text <- html_text(r, trim = TRUE)
      # Извлекаем число из строки вида "❤ 3" или "❤3" или просто "3"
      num <- as.numeric(str_extract(r_text, "\\d+$"))
      if (!is.na(num)) total_reactions <- total_reactions + num
    }
  }
  
  # Если div.reactions не найден — пробуем найти реакции в атрибутах title
  if (total_reactions == 0) {
    # Ищем все элементы с классом, содержащим "reaction"
    all_react <- node %>% html_elements("[class*='reaction']")
    for (r in all_react) {
      r_text <- html_text(r, trim = TRUE)
      num <- as.numeric(str_extract(r_text, "\\d+"))
      if (!is.na(num)) total_reactions <- total_reactions + num
    }
  }
  
  # --- 4. ПЕРЕСЫЛКА ---
  # CSS-селектор: div.fwd_from или div.forwarded_from
  fwd_node <- node %>% html_element("div.fwd_from, div.forwarded_from")
  is_forwarded <- !is.na(fwd_node)
  
  # --- 5. ОЧИСТКА ТЕКСТА ---
  clean_text <- str_squish(text_content)
  
  # --- 6. КОЛИЧЕСТВО СЛОВ ---
  word_count <- length(str_split(clean_text, "\\s+")[[1]])
  
  # --- 7. КАТЕГОРИЯ ---
  category <- "Прочее"
  if (is_forwarded) {
    category <- "Пересланный пост"
  } else if (str_detect(clean_text, regex("\\b(Lusine|Лусине)\\b", ignore_case = TRUE))) {
    category <- "Личное (Lusine)"
  } else if (str_detect(clean_text, "«|»") || str_detect(clean_text, "—\\s*[А-ЯA-Z][а-яa-z]+")) {
    category <- "Цитата"
  }
  
  # --- 8. ДОБАВЛЕНИЕ В ТАБЛИЦУ (методичка, 04/ШАГ 4 — rbind) ---
  new_row <- data.frame(
    date = date_str,
    text = clean_text,
    total_reactions = total_reactions,
    word_count = word_count,
    category = category,
    is_forwarded = is_forwarded,
    stringsAsFactors = FALSE
  )
  df <- rbind(df, new_row)
}

cat("Обработано постов:", nrow(df), "\n\n")

# ==========================================================
# ШАГ 4: Расчёт метрик
# ==========================================================
df <- df %>% filter(word_count > 5)

df$efficiency <- ifelse(df$word_count > 0,
                        (df$total_reactions / df$word_count) * 100,
                        0)

# Парсим дату для временного анализа
df$date_parsed <- dmy(df$date, quiet = TRUE)

cat("=== ДИАГНОСТИКА ===\n")
cat("Всего постов:", nrow(df), "\n")
cat("Постов с реакциями > 0:", sum(df$total_reactions > 0), "\n")
cat("Максимум реакций:", max(df$total_reactions), "\n")
cat("Сумма всех реакций:", sum(df$total_reactions), "\n")
cat("Категории:\n")
print(table(df$category))
cat("\n")

# ==========================================================
# ШАГ 5: Агрегация и визуализация (ggplot2)
# ==========================================================
agg_df <- df %>%
  group_by(category) %>%
  summarise(
    total_posts = n(),
    avg_reactions = mean(total_reactions, na.rm = TRUE),
    median_reactions = median(total_reactions, na.rm = TRUE),
    max_reactions = max(total_reactions, na.rm = TRUE),
    avg_words = mean(word_count, na.rm = TRUE),
    avg_efficiency = mean(efficiency, na.rm = TRUE)
  ) %>%
  ungroup() %>%
  mutate(across(where(is.numeric), round, 2))

cat("\nСводная таблица вовлеченности:\n")
print(agg_df)

# График 1: Средние реакции по категориям
plot1 <- ggplot(agg_df, aes(x = reorder(category, -avg_reactions), y = avg_reactions, fill = category)) +
  geom_bar(stat = "identity", width = 0.6) +
  geom_text(aes(label = avg_reactions), vjust = -0.5, size = 4) +
  labs(
    title = "Рисунок 1. Средняя вовлеченность (реакции) по типу контента",
    x = "Категория поста",
    y = "Среднее количество реакций"
  ) +
  theme_minimal() +
  theme(legend.position = "none", plot.title = element_text(hjust = 0.5))

# График 2: Boxplot эффективности
plot2 <- ggplot(df, aes(x = category, y = efficiency, fill = category)) +
  geom_boxplot(alpha = 0.7, outlier.color = "red", outlier.size = 2) +
  labs(
    title = "Рисунок 2. Распределение эффективности реакций (на 100 слов)",
    x = "Категория поста",
    y = "Реакций на 100 слов"
  ) +
  theme_minimal() +
  theme(legend.position = "none", plot.title = element_text(hjust = 0.5))

# График 3: Распределение категорий
plot3 <- ggplot(df, aes(x = category, fill = category)) +
  geom_bar() +
  geom_text(stat = "count", aes(label = after_stat(count)), vjust = -0.5) +
  labs(
    title = "Рисунок 3. Распределение постов по категориям",
    x = "Категория",
    y = "Количество постов"
  ) +
  theme_minimal() +
  theme(legend.position = "none", plot.title = element_text(hjust = 0.5))

print(plot1)
print(plot2)
print(plot3)

# Топ-5 постов
cat("\nТоп-5 самых реактивных постов:\n")
top_posts <- df %>%
  arrange(desc(total_reactions)) %>%
  head(5) %>%
  select(category, total_reactions, word_count, text) %>%
  mutate(text = str_sub(text, 1, 70))
print(top_posts)

# ==========================================================
# ШАГ 6: Сохранение данных (методичка, 04/ШАГ 4 — write_csv)
# ==========================================================
write.csv(df, "/content/flight_of_the_soul_data.csv", row.names = FALSE)
cat("\nДанные сохранены в /content/flight_of_the_soul_data.csv\n")