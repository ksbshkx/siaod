import random
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import Button, END, Text, StringVar, OptionMenu

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


# Проверка пересечений
def is_time_overlap(start1, end1, routes):
    for start2, end2 in routes:
        if max(start1, start2) < min(end1, end2):
            return True
    return False


# Расчет времени окончания маршрута
def calculate_route_end(start_time, route_duration):
    full_datetime = datetime.combine(datetime.today(), start_time) + route_duration
    return full_datetime.time()


# Отображение расписания
def display_schedule(schedule):
    schedule_text.delete(1.0, END)
    for driver, routes in schedule.items():
        schedule_text.insert(END, f"Водитель: {driver}\n")
        for start, end in routes:
            schedule_text.insert(END, f"  Рейс с {start.strftime('%H:%M')} до {end.strftime('%H:%M')}\n")
        schedule_text.insert(END, "\n")


# Генетический алгоритм
def fitness(schedule, driver_list):
    routes_assigned = sum(len(routes) for routes in schedule.values())
    penalties = 0
    for driver, routes in schedule.items():
        for i in range(1, len(routes)):
            prev_end = routes[i - 1][1]
            curr_start = routes[i][0]
            if datetime.combine(datetime.today(), curr_start) - datetime.combine(datetime.today(),
                                                                                 prev_end) < timedelta(minutes=15):
                penalties += 1
    return routes_assigned - penalties


def create_population(driver_list, num_routes):
    population = []
    for _ in range(50):
        schedule = {driver: [] for driver in driver_list}
        routes = generate_route_times()[:num_routes]
        random.shuffle(routes)
        for route_start in routes:
            route_end = calculate_route_end(route_start, traffic_route_time)
            driver = random.choice(driver_list)
            schedule[driver].append((route_start, route_end))
        population.append(schedule)
    return population


def crossover(parent1, parent2, driver_list):
    child = {driver: [] for driver in driver_list}
    for driver in driver_list:
        if random.random() > 0.5:
            child[driver] = parent1[driver]
        else:
            child[driver] = parent2[driver]
    return child


def mutate(schedule, driver_list):
    driver = random.choice(driver_list)
    if schedule[driver]:
        schedule[driver].pop(random.randint(0, len(schedule[driver]) - 1))
    route_start = random.choice(generate_route_times())
    route_end = calculate_route_end(route_start, traffic_route_time)
    schedule[driver].append((route_start, route_end))
    return schedule


def genetic_algorithm(driver_list, num_routes):
    population = create_population(driver_list, num_routes)
    generations = 100
    for _ in range(generations):
        population = sorted(population, key=lambda x: fitness(x, driver_list), reverse=True)
        next_population = population[:10]
        while len(next_population) < 50:
            parent1, parent2 = random.sample(population[:20], 2)
            child = crossover(parent1, parent2, driver_list)
            if random.random() < 0.1:
                child = mutate(child, driver_list)
            next_population.append(child)
        population = next_population
    return max(population, key=lambda x: fitness(x, driver_list))


# Генерация расписания
def generate_schedule_genetic():
    try:
        num_routes = int(num_routes_entry.get())
        driver_type = driver_type_var.get()
        drivers = drivers_A if driver_type == "A" else drivers_B

        if not drivers:
            raise ValueError(f"Нет водителей типа {driver_type} для создания расписания.")

        schedule = genetic_algorithm(drivers, num_routes)
        display_schedule(schedule)
    except ValueError as e:
        schedule_text.insert(END, f"\nОшибка: {e}\n")


# Интерфейс
root = tk.Tk()
root.title("Генератор расписания (генетический алгоритм)")
root.geometry("700x600")

driver_type_var = StringVar(value="A")
OptionMenu(root, driver_type_var, "A", "B").pack()

num_routes_entry = tk.Entry(root)
num_routes_entry.insert(0, "10")
num_routes_entry.pack()

schedule_text = Text(root, width=80, height=20)
schedule_text.pack()

generate_button = Button(root, text="Сгенерировать расписание", command=generate_schedule_genetic)
generate_button.pack()

root.mainloop()
