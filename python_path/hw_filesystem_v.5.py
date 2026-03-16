#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Анализатор логов покупок
Версия 3.0 с конфигурацией в начале (вынесение настроек в отдельное место)
Версия 4.0 с правильной обработкой CSV (проблема экранирования CSV)
Версия 5.0 переносимая версия с относительными путями
"""

from pathlib import Path
import json
import csv  # ← подключаем модуль csv
from datetime import datetime

# ============================================================================
# КОНФИГУРАЦИЯ - переносимая
# ============================================================================

# Корень проекта - папка, где лежит этот скрипт
BASE_PATH = Path(__file__).parent

# Папки относительно корня проекта
INPUT_DIR = BASE_PATH / 'Downloads'     # исходные данные
OUTPUT_DIR = BASE_PATH                   # результаты
REPORTS_DIR = BASE_PATH / 'reports'      # статистика

# Имена файлов
PURCHASE_FILE = 'purchase_log.txt'
VISIT_FILE = 'visit_log.csv'
FUNNEL_FILE = 'funnel.csv'
STATS_FILE = f'statistics_{datetime.now().strftime("%Y%m%d_%H%M")}.json'

# Настройки обработки
ENCODING = 'utf-8-sig'
PROGRESS_STEP = 100000
USER_ID_COLUMN = 0  # индекс колонки с user_id

# ============================================================================
# КОД ПРОГРАММЫ
# ============================================================================

print("=" * 70)
print(" АНАЛИЗАТОР ЛОГОВ (переносимая версия)")
print("=" * 70)
print(f" Корень проекта: {BASE_PATH}")
print(f" Читаем из:      {INPUT_DIR}")
print(f" Пишем в:        {OUTPUT_DIR}")
print("=" * 70)

# Создаем нужные папки
REPORTS_DIR.mkdir(exist_ok=True)

# Пути к файлам
purchase_path = INPUT_DIR / PURCHASE_FILE
visits_path = INPUT_DIR / VISIT_FILE
funnel_path = OUTPUT_DIR / FUNNEL_FILE
stats_path = REPORTS_DIR / STATS_FILE

print("=" * 70)
print(" ЗАПУСК АНАЛИЗАТОРА ЛОГОВ (CSV версия)")
print("=" * 70)

# ----------------------------------------------------------------------------
# ЗАДАНИЕ 1: Загрузка purchase_log.txt 
# ----------------------------------------------------------------------------
print("\n [1/2] Загрузка данных о покупках...")

purchases = {}

try:
    with open(purchase_path, 'r', encoding=ENCODING) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            try:
                purchase_data = json.loads(line)
                user_id = purchase_data.get('user_id')
                category = purchase_data.get('category')
                
                if user_id and category:
                    purchases[user_id] = category
            except json.JSONDecodeError:
                continue
    
    print(f"     Загружено {len(purchases):,} записей о покупках")

except FileNotFoundError:
    print(f"    X Ошибка: файл {purchase_path} не найден!")
    purchases = {}

# ----------------------------------------------------------------------------
# ЗАДАНИЕ 2: Обработка visit_log.csv с использованием модуля csv
# ----------------------------------------------------------------------------
print("\n [2/2] Обработка лога визитов (с csv модулем)...")

total_visits = 0
visits_with_purchase = 0
unique_buyers = set()

try:
    with open(visits_path, 'r', encoding=ENCODING, newline='') as f_in, \
         open(funnel_path, 'w', encoding=ENCODING, newline='') as f_out:
        
        # Создаем reader и writer для правильной обработки CSV
        csv_reader = csv.reader(f_in)
        csv_writer = csv.writer(f_out)
        
        # Читаем заголовок
        header = next(csv_reader)
        # Добавляем новую колонку
        new_header = header + ['category']
        csv_writer.writerow(new_header)
        print(f"     Заголовок: {new_header}")
        
        # Обрабатываем данные
        for row_num, row in enumerate(csv_reader, start=2):
            if not row:  # пропускаем пустые строки
                continue
            
            total_visits += 1
            
            # Проверяем, что в строке достаточно колонок
            if len(row) <= USER_ID_COLUMN:
                print(f"      Строка {row_num}: недостаточно колонок, пропускаем")
                continue
            
            user_id = row[USER_ID_COLUMN]
            
            # Проверяем, есть ли покупка
            if user_id in purchases:
                visits_with_purchase += 1
                unique_buyers.add(user_id)
                
                # Добавляем категорию и записываем
                new_row = row + [purchases[user_id]]
                csv_writer.writerow(new_row)
            
            # Прогресс
            if PROGRESS_STEP > 0 and total_visits % PROGRESS_STEP == 0:
                print(f"     Обработано {total_visits:,} строк...")
    
    print(f"     Обработка завершена!")

except FileNotFoundError:
    print(f"    X Ошибка: файл {visits_path} не найден!")
except Exception as e:
    print(f"    X Ошибка при обработке: {e}")

# ----------------------------------------------------------------------------
# СТАТИСТИКА
# ----------------------------------------------------------------------------
print("\n" + "=" * 70)
print(" ИТОГИ ОБРАБОТКИ")
print("=" * 70)

if total_visits > 0:
    conversion = (visits_with_purchase / total_visits) * 100
    print(f"   Всего обработано визитов: {total_visits:>12,}")
    print(f"   Визиты с покупками:       {visits_with_purchase:>12,}")
    print(f"   Уникальных покупателей:   {len(unique_buyers):>12,}")
    print(f"   Конверсия в покупку:      {conversion:>11.2f}%")

# Сохраняем статистику
stats = {
    'timestamp': datetime.now().isoformat(),
    'total_visits': total_visits,
    'visits_with_purchase': visits_with_purchase,
    'unique_buyers': len(unique_buyers),
    'conversion_percent': round(conversion, 2) if total_visits else 0,
}

with open(stats_path, 'w', encoding=ENCODING) as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

print(f"\n Результаты: {funnel_path}")
print(f" Статистика: {stats_path}")
print("=" * 70)