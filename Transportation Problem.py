import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import linprog

# Функція для створення полів введення таблиці
def create_table_entries():
    global cost_entries, demand_entries, supply_entries
    # Очищення старих віджетів у фреймі
    for widgets in frame.winfo_children():
        widgets.destroy()
    
    # Заголовки таблиць
    ttk.Label(frame, text="Витрати").grid(row=0, column=0, columnspan=num_variables)
    ttk.Label(frame, text="Обмеження").grid(row=0, column=num_variables+1)

    # Створення таблиці для введення витрат
    cost_entries = []
    for i in range(num_constraints):
        row = []
        for j in range(num_variables):
            entry = ttk.Entry(frame, width=5)
            entry.grid(row=i+1, column=j)
            row.append(entry)
        cost_entries.append(row)

    # Створення таблиці для введення обмежень
    supply_entries = []
    for i in range(num_constraints):
        entry = ttk.Entry(frame, width=5)
        entry.grid(row=i+1, column=num_variables+1)
        supply_entries.append(entry)

    # Заголовок таблиці для введення потреб
    ttk.Label(frame, text="Потреби").grid(row=num_constraints+1, column=0, columnspan=num_variables)
    
    # Створення таблиці для введення потреб
    demand_entries = []
    for i in range(num_variables):
        entry = ttk.Entry(frame, width=5)
        entry.grid(row=num_constraints+2, column=i)
        demand_entries.append(entry)

    # Кнопка для розв'язання задачі
    solve_button = ttk.Button(frame, text="Розв'язати", command=solve_transport_problem)
    solve_button.grid(row=num_constraints+3, column=0, columnspan=num_variables + 2, pady=10)

# Функція для встановлення розміру таблиці
def set_table_size():
    global num_variables, num_constraints
    try:
        num_variables = int(variable_entry.get())
        num_constraints = int(constraint_entry.get())
        create_table_entries()
    except ValueError:
        messagebox.showerror("Помилка", "Будь ласка, введіть правильні числові значення для розмірів таблиці")

# Функція для розв'язання транспортної задачі
def solve_transport_problem():
    try:
        N = int(N_entry.get())  # Кількість кроків (точність)
        percentage = 1 - int(percentage_var.get()) / 100  # Відсоток згоди споживача на зменшення потреб
        
        # Зчитування даних із таблиць
        c = []
        for i in range(num_constraints):
            for j in range(num_variables):
                c.append(float(cost_entries[i][j].get()))

        initial_b = []
        for i in range(num_variables):
            initial_b.append(float(demand_entries[i].get()))

        b_ub = []
        for i in range(num_constraints):
            b_ub.append(float(supply_entries[i].get()))

        initial_b = np.array(initial_b)
        b_half = initial_b * percentage  # Мінімальні потреби споживача
        difference = initial_b - b_half

        # Створення матриці обмежень для задачі лінійного програмування
        A_ub = []
        for i in range(num_constraints):
            row = [0] * (num_variables * num_constraints)
            for j in range(num_variables):
                row[i * num_variables + j] = 1
            A_ub.append(row)

        A_eq = []
        for j in range(num_variables):
            row = [0] * (num_variables * num_constraints)
            for i in range(num_constraints):
                row[i * num_variables + j] = -1
            A_eq.append(row)

        limit = (sum(b_ub) - (sum(initial_b) - sum(initial_b) * percentage)) / (sum(initial_b) - (sum(initial_b) - sum(initial_b) * percentage))

        results = []

        for k in range(N + 1):
            if k / N > limit:
                break
            else:
                b = [(k / N) * (initial_b[j] - difference[j]) + difference[j] for j in range(num_variables)]
            b = [-x for x in b]
            b_eq = np.array(b)

            # Виконання лінійного програмування
            result = linprog(c, A_ub=A_ub, b_ub=b_ub, A_eq=A_eq, b_eq=b_eq, bounds=(0, None), method='simplex')
            b = [-x for x in b]
            if result.success:
                results.append((k, result.fun, result.x, b))
            else:
                results.append((k, None, None, None))
                result_textbox.insert(tk.END, f"Крок {k}: Розв'язок не знайдено\n")

        costs = [result[1] for result in results if result[1] is not None]

        if costs:
            max_cost = max(costs)
            min_cost = min(costs)

            percent_values = []
            mu_values = []
            reliability_values = []
            b_values = []
            x_values = []
            cost_values = []

            for k, cost, x, b in results:
                if cost is not None:
                    mu = (max_cost - cost) / (max_cost - min_cost)
                    reliability = k / N
                    percent = int(percentage_var.get()) + (reliability * (100 - int(percentage_var.get())))
                    percent_values.append(percent)
                    mu_values.append(mu)
                    reliability_values.append(reliability)
                    b_values.append(b)
                    x_values.append(x)
                    cost_values.append(cost)
        
            # Очищення попередніх результатів
            for widgets in result_table_frame.winfo_children():
                widgets.destroy()

            # Вивід заголовків таблиці результатів
            headers = ["Номер кроку", "Надійність потреб", "Потреби споживачів", "Мінімальні витрати", "Надійність функції цілі"]
            for col, header in enumerate(headers):
                ttk.Label(result_table_frame, text=header).grid(row=0, column=col)

            for k, reliability, b, cost, mu in zip(range(N + 1), reliability_values, b_values, cost_values, mu_values):
                ttk.Label(result_table_frame, text=k).grid(row=k+1, column=0)
                ttk.Label(result_table_frame, text=f"{reliability:.2f}").grid(row=k+1, column=1)
                ttk.Label(result_table_frame, text=f"{b}").grid(row=k+1, column=2)
                ttk.Label(result_table_frame, text=f"{cost:.2f}").grid(row=k+1, column=3)
                ttk.Label(result_table_frame, text=f"{mu:.2f}").grid(row=k+1, column=4)

            intersection_x = None
            intersection_y = None
            intersection_index = None
            for i in range(1, len(percent_values)):
                if (mu_values[i - 1] >= reliability_values[i - 1] and mu_values[i] <= reliability_values[i]) or \
                        (mu_values[i - 1] <= reliability_values[i - 1] and mu_values[i] >= reliability_values[i]):
                    intersection_x = percent_values[i]
                    intersection_y = mu_values[i]
                    intersection_index = i
                    break

            if intersection_index is not None:
                result_text = f"Значення функції цілі: {intersection_y:.2f}\n"
                result_text += f"Рівень забезпеченості: {percent_values[intersection_index]:.2f}%\n"
                result_text += f"Потреби споживачів: {b_values[intersection_index]}\n"
                result_text += f"Оптимальний план підвезення: {x_values[intersection_index]}\n"
                result_text += f"Оптимальна вартість: {cost_values[intersection_index]:.2f}\n"
                result_textbox.delete(1.0, tk.END)
                result_textbox.insert(tk.END, result_text)
            else:
                result_textbox.delete(1.0, tk.END)
                result_text = ""
                if int(percentage_var.get()) == 100:
                    result_text += "Споживач не згоден на зменшення поставок.\n"
                if sum(b_ub) == sum(initial_b):
                    result_text += f"Умову балансу дотримано.\n"
                if sum(b_ub) > sum(initial_b):
                    result_text += f"Запасів більше, ніж потреб\n"
                result_text += f"Потреби споживачів: {initial_b}\n"
                result_text += f"Оптимальний план підвезення: {x_values[-1]}\n"
                result_text += f"Оптимальна вартість: {cost_values[-1]:.2f}\n"
                result_textbox.insert(tk.END, result_text)

            # Візуалізація результатів
            plt.figure(figsize=(10, 6))
            plt.plot(percent_values, mu_values, marker='o', label='Надійність функції цілі (μ_Ц(k^x))')
            plt.plot(percent_values, reliability_values, marker='x', label='Надійність споживачів')
            if intersection_x is not None and intersection_y is not None:
                plt.axvline(x=intersection_x, color='r', linestyle='--')
                plt.axhline(y=intersection_y, color='r', linestyle='--')
                plt.scatter(intersection_x, intersection_y, color='red')
                plt.text(intersection_x, intersection_y, f'({intersection_x:.2f}, {intersection_y:.2f})', color='red')

            plt.xlim(0, 100)
            plt.ylim(0, 1)
            plt.xlabel('Рівень потреб у відсотках від максимального (%)')
            plt.ylabel('Надійність')
            plt.title('Графік ступеня впевненості в тому, що план ефективний за витратами та рівнем забезпечення споживачів')
            plt.legend()
            plt.grid(True)

            plt.xticks(np.arange(0, 101, 10))
            plt.yticks(np.arange(0, 1.1, 0.1))

            plt.show()
        else:
            result_textbox.insert(tk.END, "Не вдалося знайти допустимий розв'язок\n")
    except ValueError:
        messagebox.showerror("Помилка", "Будь ласка, введіть коректні числові значення")

# Налаштування основного вікна програми
app = tk.Tk()
app.title("Транспортна задача з нечіткими потребами в матеріальних ресурсах")

# Налаштування фрейму для введення розмірів таблиці
size_frame = ttk.Frame(app)
size_frame.pack(padx=10, pady=10)

ttk.Label(size_frame, text="Кількість споживачів:").grid(row=0, column=0)
variable_entry = ttk.Entry(size_frame, width=5)
variable_entry.grid(row=0, column=1)

ttk.Label(size_frame, text="Кількість постачальників:").grid(row=1, column=0)
constraint_entry = ttk.Entry(size_frame, width=5)
constraint_entry.grid(row=1, column=1)

ttk.Label(size_frame, text="Кількість кроків N (точність):").grid(row=2, column=0)
N_entry = ttk.Entry(size_frame, width=5)
N_entry.grid(row=2, column=1)

ttk.Label(size_frame, text="Відсоток згоди споживача:").grid(row=3, column=0)
percentage_var = tk.StringVar(value="50")
percentage_menu = ttk.Combobox(size_frame, textvariable=percentage_var, values=[str(i) for i in range(10, 101, 10)])
percentage_menu.grid(row=3, column=1)

size_button = ttk.Button(size_frame, text="Встановити розмір таблиці", command=set_table_size)
size_button.grid(row=4, column=0, columnspan=2, pady=10)

# Налаштування фрейму для таблиці введення даних
frame = ttk.Frame(app)
frame.pack(padx=10, pady=10)

# Налаштування фрейму для виведення результатів
result_frame = ttk.Frame(app)
result_frame.pack(padx=10, pady=10, fill='both', expand=True)

ttk.Label(result_frame, text="Результати:").pack(anchor='w')
result_textbox = tk.Text(result_frame, height=10, width=80)
result_textbox.pack(fill='both', expand=True)

# Створення області з прокруткою для таблиці результатів
result_table_canvas = tk.Canvas(app)
result_table_scrollbar = ttk.Scrollbar(app, orient="vertical", command=result_table_canvas.yview)
result_table_scrollbar.pack(side="right", fill="y")
result_table_canvas.pack(side="left", fill="both", expand=True)
result_table_canvas.configure(yscrollcommand=result_table_scrollbar.set)

result_table_frame = ttk.Frame(result_table_canvas)
result_table_canvas.create_window((0, 0), window=result_table_frame, anchor="nw")

# Оновлення розмірів області з прокруткою
def on_configure(event):
    result_table_canvas.configure(scrollregion=result_table_canvas.bbox("all"))

result_table_frame.bind("<Configure>", on_configure)

# Встановлення початкових значень для кількості змінних та обмежень
num_variables = 4
num_constraints = 3

app.mainloop()
