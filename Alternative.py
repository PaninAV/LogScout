import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import pandas as pd
import subprocess

# Словарь ключевых слов для фильтрации событий
keywords = {
    "AUTH_SUCCESS": ["Accepted password", "session opened"],
    "AUTH_FAILURE": ["authentication failure", "Failed password"],
    "SUDO": ["sudo", "COMMAND="],
    "SSH_CONNECT": ["sshd", "Accepted", "session opened"],
    "SSH_FAILED": ["sshd", "Failed password", "authentication failure"],
    "USERADD": ["useradd"],
    "USERDEL": ["userdel"],
    "GROUPMOD": ["groupadd", "groupdel", "groupmod"],
    "SU_ATTEMPT": ["su:"],
    "CRON": ["CRON", "cron"],
    "SERVICE": ["systemd", "Started", "Stopped", "Failed"],
    "APT": ["apt", "apt-get", "install", "remove", "upgrade"]
}

# Проверка строки на соответствие категории
def matches_keywords(event_type, line):
    if event_type == "ALL":
        return True
    if event_type not in keywords:
        return False
    return any(word in line for word in keywords[event_type])

# Извлечение событий
def extract_events(event_type, since, until):
    cmd = ["journalctl", "--since", since, "--until", until]
    result = subprocess.run(cmd, capture_output=True, text=True)
    logs = result.stdout.splitlines()

    filtered = []
    for line in logs:
        if matches_keywords(event_type, line):
            filtered.append({"timestamp": line[:15], "message": line})
    return filtered

# Экспорт в файл
def export(events, fmt):
    if not events:
        messagebox.showwarning("Нет данных", "Сначала извлеките события.")
        return

    filetypes = [("CSV files", "*.csv")] if fmt == "csv" else [("Excel files", "*.xlsx")]
    f = filedialog.asksaveasfilename(defaultextension=f".{fmt}", filetypes=filetypes)

    if f:
        df = pd.DataFrame(events)
        if fmt == "csv":
            df.to_csv(f, index=False)
        else:
            df.to_excel(f, index=False)
        messagebox.showinfo("Готово", f"События сохранены в {f}")

# GUI
root = tk.Tk()
root.title("LogScout GUI")
root.geometry("950x600")  # увеличил размер окна

# Переменная для хранения событий
events_data = []

# === Верхняя панель управления ===
frame_controls = ttk.Frame(root)
frame_controls.pack(pady=10, fill="x")

# Тип события
ttk.Label(frame_controls, text="Тип события:").grid(row=0, column=0, padx=5)
event_var = tk.StringVar()
event_menu = ttk.Combobox(frame_controls, textvariable=event_var, state="readonly", width=25)
event_menu["values"] = [
    "ALL", "AUTH_SUCCESS", "AUTH_FAILURE", "SUDO", "SSH_CONNECT", "SSH_FAILED",
    "USERADD", "USERDEL", "GROUPMOD", "SU_ATTEMPT", "CRON", "SERVICE", "APT"
]
event_menu.current(0)
event_menu.grid(row=0, column=1, padx=5)

# Даты
ttk.Label(frame_controls, text="С (YYYY-MM-DD HH:MM):").grid(row=1, column=0, padx=5)
since_entry = ttk.Entry(frame_controls, width=25)
since_entry.insert(0, "2025-08-01 00:00")
since_entry.grid(row=1, column=1, padx=5)

ttk.Label(frame_controls, text="По (YYYY-MM-DD HH:MM):").grid(row=2, column=0, padx=5)
until_entry = ttk.Entry(frame_controls, width=25)
until_entry.insert(0, "2025-08-04 23:59")
until_entry.grid(row=2, column=1, padx=5)

# === Кнопки управления ===
frame_buttons = ttk.Frame(root)
frame_buttons.pack(pady=5)

def on_extract():
    global events_data
    e_type = event_var.get()
    since = since_entry.get()
    until = until_entry.get()
    try:
        datetime.strptime(since, "%Y-%m-%d %H:%M")
        datetime.strptime(until, "%Y-%m-%d %H:%M")
    except ValueError:
        messagebox.showerror("Ошибка даты", "Введите дату в формате YYYY-MM-DD HH:MM")
        return

    events_data = extract_events(e_type, since, until)

    # Очистить таблицу
    for i in tree.get_children():
        tree.delete(i)

    # Добавить новые данные
    for event in events_data:
        tree.insert("", "end", values=(event["timestamp"], event["message"]))

    status_var.set(f"Извлечено {len(events_data)} событий.")

def clear_table():
    global events_data
    events_data = []
    for i in tree.get_children():
        tree.delete(i)
    status_var.set("Таблица очищена.")

ttk.Button(frame_buttons, text="Извлечь артефакты", command=on_extract).grid(row=0, column=0, padx=10)
ttk.Button(frame_buttons, text="Сохранить в CSV", command=lambda: export(events_data, "csv")).grid(row=0, column=1, padx=10)
ttk.Button(frame_buttons, text="Сохранить в Excel", command=lambda: export(events_data, "excel")).grid(row=0, column=2, padx=10)
ttk.Button(frame_buttons, text="Очистить таблицу", command=clear_table).grid(row=0, column=3, padx=10)

# === Таблица ===
frame_table = ttk.Frame(root)
frame_table.pack(fill="both", expand=True, pady=10)

tree = ttk.Treeview(frame_table, columns=("timestamp", "message"), show="headings", height=15)
tree.heading("timestamp", text="Время")
tree.heading("message", text="Сообщение")
tree.column("timestamp", width=150, anchor="w")
tree.column("message", width=750, anchor="w")

scroll_y = ttk.Scrollbar(frame_table, orient="vertical", command=tree.yview)
scroll_x = ttk.Scrollbar(frame_table, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

tree.grid(row=0, column=0, sticky="nsew")
scroll_y.grid(row=0, column=1, sticky="ns")
scroll_x.grid(row=1, column=0, sticky="ew")

frame_table.rowconfigure(0, weight=1)
frame_table.columnconfigure(0, weight=1)

# === Статусная строка ===
status_var = tk.StringVar()
status_var.set("Готово.")
status_bar = ttk.Label(root, textvariable=status_var, relief="sunken", anchor="w")
status_bar.pack(fill="x", side="bottom")

root.mainloop()
