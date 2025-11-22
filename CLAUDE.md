# Принципы проектирования высокоуровневых инструментов для агентов

## 1. Разделение ответственности

| Компонент | Ответственность |
|-----------|-----------------|
| **Инструмент (обёртка)** | Выполнить цепочку API-вызовов, собрать данные, обработать ошибки, вернуть структурированный результат |
| **Агент (LLM)** | Анализировать данные, учитывать контекст задачи, принимать решения |

**Инструмент НЕ принимает решений** — только возвращает факты. Агент решает, что "лучше" исходя из условий задачи.

---

## 2. Именование инструментов

Имя должно объяснять агенту **что на входе → что делает → что на выходе**:

```
Req_Test_Options_For_Parameters
     │         │           │
     │         │           └── что на входе
     │         └── что делает
     └── префикс запроса
```

**Примеры:**
- `Req_Test_TimeSlots_For_Participants` — проверить слоты для участников
- `Req_Find_Available_Rooms_For_TimeRange` — найти свободные комнаты
- `Req_Compare_Prices_For_Configurations` — сравнить цены конфигураций

**Конвенция уровней:**
- Высокоуровневые: `Req_Test_*`, `Req_Find_*`, `Req_Compare_*`, `Req_Calculate_*` — агрегируют вызовы
- Низкоуровневые: `Req_Create*`, `Req_Update*`, `Req_Delete*`, `Req_Get*` — прямые операции

---

## 3. Управление состоянием

- **Не пытаемся сохранить/восстановить исходное состояние** — сложно и ненадёжно
- **Приводим состояние к известному перед началом работы** — гарантируем чистый старт
- **Оставляем состояние чистым/нейтральным на выходе** — через `finally`
- **Агент адаптируется к изменениям среды** — это его задача, не инструмента

---

## 4. Оптимизация вызовов

Структура циклов минимизирует дорогие операции:

```python
for primary_param in primary_params:       # ВНЕШНИЙ — дорогая операция (сброс/инициализация)
    reset_state()
    setup(primary_param)                   # 1 раз на primary_param

    for secondary_param in secondary_params:  # ВНУТРЕННИЙ — дешёвая операция
        apply(secondary_param)             # быстро, без пересоздания
        read_result()
        revert(secondary_param)
```

**Принцип:** дорогие операции — во внешнем цикле, дешёвые — во внутреннем.

---

## 5. Обработка ошибок

**Два типа ошибок:**

| Тип | Где возникает | Действие |
|-----|---------------|----------|
| **Фатальная** | Вне циклов (инициализация, сброс) | Завершить, вернуть `fatal_error` |
| **Локальная** | Внутри цикла (применение параметра) | Записать в `results`, продолжить |

**Структура ошибки:**
```python
class ErrorInfo(BaseModel):
    method: str          # какой метод упал
    error_text: str      # текст ошибки
    params: dict         # параметры, вызвавшие ошибку
```

Агент видит ошибки в контексте параметров и принимает решение (ресурс недоступен vs параметр невалиден — разные действия).

---

## 6. Формат ответа

```python
class Resp_Test_Options_For_Parameters(BaseModel):
    success: bool                              # общий статус выполнения
    results: Optional[List[TestResult]]        # массив результатов
    fatal_error: Optional[ErrorInfo]           # если фатальная ошибка

class TestResult(BaseModel):
    primary_param: Any                         # значение внешнего параметра
    secondary_param: Any                       # значение внутреннего параметра
    success: bool                              # успех/неуспех этой комбинации
    data: Optional[ResponseModel]              # данные ответа (если success)
    error: Optional[ErrorInfo]                 # данные ошибки (если не success)
```

---

## 7. Промптинг агента

```
## Available Tools

### High-level tools (Req_Test_*, Req_Find_*, Req_Compare_*)
Aggregate multiple API calls, return structured results for analysis.
Use for exploring options, testing combinations, comparing alternatives.
These tools reset state before and after execution.

### Low-level tools (Req_Create*, Req_Update*, Req_Delete*, Req_Get*)
Direct API operations that modify or read state.
Use for final actions after you've decided what to do.

## Guidelines

1. PREFER high-level tools for exploration and comparison
2. Use low-level tools ONLY for final actions
3. High-level tools return raw data — YOU decide what's "best" based on task
4. Errors in results are informational (resource busy, param invalid) — analyze and adapt
5. After high-level tool call, state is clean — ready for next action
```

---

## 8. Шаблон реализации инструмента

```python
def high_level_tool(api, primary_params, secondary_params) -> Response:
    results = []

    try:
        for primary in primary_params:
            # Сброс/инициализация (дорогая операция)
            try:
                reset_state(api)
                setup(api, primary)
            except ApiException as e:
                return Response(
                    success=False,
                    fatal_error=ErrorInfo(method="setup", error_text=str(e), params=None)
                )

            # Перебор вторичных параметров (дешёвые операции)
            for secondary in secondary_params:
                try:
                    apply(api, secondary)
                    data = read_result(api)
                    revert(api, secondary)

                    results.append(TestResult(
                        primary_param=primary,
                        secondary_param=secondary,
                        success=True,
                        data=data
                    ))
                except ApiException as e:
                    results.append(TestResult(
                        primary_param=primary,
                        secondary_param=secondary,
                        success=False,
                        error=ErrorInfo(
                            method="apply",
                            error_text=str(e),
                            params={"primary": primary, "secondary": secondary}
                        )
                    ))
                    try:
                        revert(api, secondary)
                    except:
                        pass

    finally:
        try:
            reset_state(api)
        except:
            pass

    return Response(success=True, results=results)
```

---

## 9. Чек-лист при создании нового инструмента

- [ ] Имя описывает вход, действие и выход
- [ ] Инструмент не принимает решений — только собирает данные
- [ ] Дорогие операции во внешнем цикле, дешёвые во внутреннем
- [ ] Состояние сбрасывается перед началом и в `finally`
- [ ] Фатальные ошибки завершают выполнение
- [ ] Локальные ошибки записываются в результаты с параметрами
- [ ] Ответ содержит достаточно информации для принятия решения агентом
