import random
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import Button, END, Text, StringVar, OptionMenu
from itertools import permutations

# Параметры времени
peak_hours = [(7, 9), (17, 19)]
non_peak_hours = [(6, 7), (9, 17), (19, 3)]
traffic_route_time = timedelta(minutes=70)
drivers_A = ["Driver_A1", "Driver_A2", "Driver_A3"]
drivers_B = ["Driver_B1", "Driver_B2"]


# Генерация маршрутов
def generate_route_times():
    route_times = []
    for start_hour, end_hour in peak_hours:
        current_time = datetime.strptime(f"{start_hour}:00", "%H:%M")
        while current_time.hour < end_hour:
            route_times.append(current_time.time())
            current_time += traffic_route_time
    for start_hour, end_hour in non_peak_hours:
        current_time = datetime.strptime(f"{start_hour}:00", "%H:%M")
        while current_time.hour < end_hour:
            route_times.append(current_time.time())
            current_time += traffic_route_time
    return random.sample(route_times, int(len(route_times) * 0.7)) + random.sample(route_times,
                                                                                   int(len(route_times) * 0.3))


# Проверка пересечений времени
def is_time_overlap(start1, end1, routes):
    for start2, end2 in routes:
        if max(start1, start2) < min(end1, end2):
            return True
    return False


# Проверка рабочего времени
def is_within_work_hours(start_time, end_time, work_start, work_end):
    if work_start <= work_end:  # Обычный день
        return work_start <= start_time and end_time <= work_end
    else:  # Переход через полночь
        return work_start <= start_time or end_time <= work_end


# Расчет времени окончания маршрута
def calculate_route_end(start_time, route_duration):
    full_datetime = datetime.combine(datetime.today(), start_time) + route_duration
    return full_datetime.time()


# Метод "в лоб"
def brute_force_schedule(driver_list, num_routes, work_hours, driver_type):
    all_routes = generate_route_times()[:num_routes]  # Генерируем маршруты
    best_schedule = None
    max_routes_assigned = 0

    # Инициализируем пустое расписание для водителей
    initial_schedule = {driver: [] for driver in driver_list}

    # Перебираем все возможные комбинации распределения маршрутов
    for perm in permutations(all_routes, len(all_routes)):
        schedule = {driver: [] for driver in driver_list}
        driver_index = 0  # Индекс текущего водителя
        routes_assigned = 0  # Счетчик успешно назначенных маршрутов

        # Пробуем назначить маршруты
        for route_start in perm:
            route_end = calculate_route_end(route_start, traffic_route_time)
            driver = driver_list[driver_index]
            work_start, work_end = work_hours[driver]

            # Проверка на пересечение времени и рабочие часы
            if (
                    not is_time_overlap(route_start, route_end, schedule[driver]) and
                    is_within_work_hours(route_start, route_end, work_start, work_end)
            ):
                if driver_type == "A":
                    # Учет 8-часового рабочего дня и обеда
                    total_work_time = sum(
                        (datetime.combine(datetime.today(), end) - datetime.combine(datetime.today(),
                                                                                    start)).seconds / 3600
                        for start, end in schedule[driver]
                    )
                    if total_work_time + 1 + traffic_route_time.seconds / 3600 > 8:  # 1 час обеда
                        continue

                if driver_type == "B":
                    # Проверка на сменность и перерыв
                    last_route = schedule[driver][-1] if schedule[driver] else None
                    if last_route:
                        last_end_time = datetime.combine(datetime.today(), last_route[1])
                        curr_start_time = datetime.combine(datetime.today(), route_start)
                        if (curr_start_time - last_end_time).seconds < 15 * 60:  # Минимальный перерыв 15 минут
                            continue

                # Назначаем маршрут
                schedule[driver].append((route_start, route_end))
                routes_assigned += 1

            # Переходим к следующему водителю
            driver_index = (driver_index + 1) % len(driver_list)

        # Сохраняем лучшее расписание
        if routes_assigned > max_routes_assigned:
            max_routes_assigned = routes_assigned
            best_schedule = schedule

    # Если ничего не найдено, возвращаем пустое расписание
    return best_schedule if best_schedule else initial_schedule


# Отображение расписания
def display_schedule(schedule):
    schedule_text.delete(1.0, END)
    for driver, routes in schedule.items():
        schedule_text.insert(END, f"Водитель: {driver}\n")
        for start, end in routes:
            schedule_text.insert(END, f"  Рейс с {start.strftime('%H:%M')} до {end.strftime('%H:%M')}\n")
        schedule_text.insert(END, "\n")


# Генерация расписания
def generate_schedule():
    try:
        num_routes = int(num_routes_entry.get())
        driver_type = driver_type_var.get()
        drivers = drivers_A if driver_type == "A" else drivers_B

        if not drivers:
            raise ValueError(f"Нет водителей типа {driver_type} для создания расписания.")

        # Устанавливаем рабочие часы для водителей
        work_hours = {
            driver: (datetime.strptime("6:00", "%H:%M").time(), datetime.strptime("3:00", "%H:%M").time())
            for driver in drivers
        }

        # Вызываем метод "в лоб"
        schedule = brute_force_schedule(drivers, num_routes, work_hours, driver_type)

        if not schedule or all(len(routes) == 0 for routes in schedule.values()):
            schedule_text.insert(END, "\nНе удалось найти подходящее расписание.\n")
        else:
            display_schedule(schedule)
    except ValueError as e:
        schedule_text.insert(END, f"\nОшибка: {e}\n")


# Интерфейс
root = tk.Tk()
root.title("Генератор расписания методом 'в лоб'")
root.geometry("700x600")

driver_type_var = StringVar(value="A")
OptionMenu(root, driver_type_var, "A", "B").pack()

num_routes_entry = tk.Entry(root)
num_routes_entry.insert(0, "10")
num_routes_entry.pack()

schedule_text = Text(root, width=80, height=20)
schedule_text.pack()

generate_button = Button(root, text="Сгенерировать расписание", command=generate_schedule)
generate_button.pack()

root.mainloop()