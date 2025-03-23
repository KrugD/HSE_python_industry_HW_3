# Тестирование проекта

## Запуск тестов

### Функциональные и модульные тесты

Проект использует `pytest` для тестирования. Чтобы запустить тесты, выполните команду:

```bash
pytest tests/
```

или для более детального вывода:

```bash
pytest -v tests/
```

### Покрытие кода тестами

Для проверки покрытия кода тестами используется `coverage`. Чтобы запустить тесты с анализом покрытия, выполните:

```bash
coverage run -m pytest
```

Затем сгенерируйте HTML-отчет:

```bash
coverage html
```

Чтобы открыть отчет о покрытии тестами, выполните команду в зависимости от вашей ОС:

#### Linux:
```bash
cd htmlcov
xdg-open index.html
```

#### macOS:
```bash
cd htmlcov
open index.html
```

#### Windows:
```cmd
cd htmlcov
start index.html
```

## Нагрузочное тестирование

Для выполнения нагрузочного тестирования используется `locust`. Запуск тестов:

```bash
locust -f tests/load_test/locustfile.py
```

После завершения тестирования отчет можно открыть следующим образом:

#### Linux:
```bash
xdg-open locust_report.html
```

#### macOS:
```bash
open locust_report.html
```

#### Windows:
```cmd
start locust_report.html
```


