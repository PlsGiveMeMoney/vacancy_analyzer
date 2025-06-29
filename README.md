# Vacancy Analyzer

Программное средство для анализа вакансий с HeadHunter и других платформ.

## Требования

- Python 3.8+
- SQLite3
- Установленные зависимости (см. ниже)
- Рекомендуется использовать PyCharm для более простой работы

## Установка

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/ваш-логин/vacancy-analyzer.git
   cd vacancy-analyzer
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

## Запуск

```bash
python main.py
```

## Настройка

Для администрирования используйте:
   - Логин: `admin`
   - Пароль: `admin1` (смените после первого входа)



## Зависимости

Основные зависимости (автоматически установятся из requirements.txt):
openpyxl==3.1.5
PyQt5==5.15.11
PyQt5_sip==12.17.0
python_bcrypt==0.3.2
Requests==2.32.4
SQLAlchemy==2.0.41

