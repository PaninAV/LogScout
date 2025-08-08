import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
import pandas as pd
import subprocess

# Функция для извлечения логов (упрощённо)
def extract_events(event_type, since, until):
    cmd = ["journalctl", "--since", since, "--until", until]
    result = subprocess.run(cmd, capture_output=True, text=True)
    logs = result.stdout.splitlines()

    filtered = []
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
    "APT": ["apt", "apt-get", "install", "remove", "upgrade"] }

    for line in logs:
    if matches_keywords(event_type, line):
        filtered.append({"timestamp": line[:15], "message": line})


def matches_keywords(event_type, line):
    if event_type == "ALL":
        return True
    if event_type not in keywords:
        return False
    return any(word in line for word in keywords[event_type])


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
root.geometry("400x300")

# Тип события
ttk.Label(root, text="Тип события:").pack(pady=5)
event_var = tk.StringVar()
event_menu = ttk.Combobox(root, textvariable=event_var)
event_menu["values"] = [
    "ALL", "AUTH_SUCCESS", "AUTH_FAILURE", "SUDO", "SSH_CONNECT", "SSH_FAILED",
    "USERADD", "USERDEL", "GROUPMOD", "SU_ATTEMPT", "CRON", "SERVICE", "APT"
]
event_menu.current(0)
event_menu.pack()

# Даты
ttk.Label(root, text="С (формат YYYY-MM-DD HH:MM):").pack()
since_entry = ttk.Entry(root)
since_entry.insert(0, "2025-08-01 00:00")
since_entry.pack()

ttk.Label(root, text="По (формат YYYY-MM-DD HH:MM):").pack()
until_entry = ttk.Entry(root)
until_entry.insert(0, "2025-08-04 23:59")
until_entry.pack()

# Кнопка извлечения
events_data = []
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
    messagebox.showinfo("Готово", f"Извлечено {len(events_data)} событий.")

ttk.Button(root, text="Извлечь артефакты", command=on_extract).pack(pady=10)

# Кнопки сохранения
ttk.Button(root, text="Сохранить в CSV", command=lambda: export(events_data, "csv")).pack(pady=5)
ttk.Button(root, text="Сохранить в Excel", command=lambda: export(events_data, "excel")).pack(pady=5)

root.mainloop()

