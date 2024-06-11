import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import threading
import sqlite3
import requests
from bs4 import BeautifulSoup

# Настройка CustomTkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Функция для создания базы данных
def create_db():
    conn = sqlite3.connect('cameras.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS cameras
                      (id INTEGER PRIMARY KEY, name TEXT, url TEXT)''')
    conn.commit()
    conn.close()

# Функция для вставки данных в базу данных
def insert_camera_data(camera_data):
    conn = sqlite3.connect('cameras.db')
    cursor = conn.cursor()
    cursor.executemany('INSERT INTO cameras (name, url) VALUES (?, ?)', camera_data)
    conn.commit()
    conn.close()

# Функция для извлечения данных из базы данных
def get_cameras_from_db():
    conn = sqlite3.connect('cameras.db')
    cursor = conn.cursor()
    cursor.execute('SELECT name, url FROM cameras')
    cameras = cursor.fetchall()
    conn.close()
    return cameras

# Функция для сбора данных с сайта
def get_camera_data(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    cameras = []

    # Пример парсинга (измените в зависимости от структуры сайта)
    for camera in soup.find_all('div', class_='camera'):
        name = camera.find('h2').text
        stream_url = camera.find('a')['href']
        cameras.append((name, stream_url))

    return cameras

# URL сайта
url = 'https://videonabludenie31.nethouse.ru/'
camera_data = get_camera_data(url)

# Создание базы данных и вставка данных
create_db()
insert_camera_data(camera_data)

class VideoApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Видео наблюдение")
        self.geometry("800x600")

        # Поле для ввода ссылки
        self.url_entry = ctk.CTkEntry(self, placeholder_text="Введите URL видеопотока")
        self.url_entry.pack(pady=20)

        # Добавление контекстного меню для копирования и вставки
        self.url_entry.bind("<Button-3>", self.show_context_menu)

        # Кнопка для запуска видеопотока
        self.start_button = ctk.CTkButton(self, text="Запустить", command=self.start_stream)
        self.start_button.pack(pady=20)

        # Кнопка для загрузки камер из базы данных
        self.load_button = ctk.CTkButton(self, text="Загрузить камеры", command=self.load_cameras)
        self.load_button.pack(pady=20)

        # Метка для отображения видеопотока
        self.video_label = ctk.CTkLabel(self)
        self.video_label.pack(pady=20)

        self.cap = None
        self.stop_event = threading.Event()

        # Создание контекстного меню
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="Копировать", command=self.copy)
        self.context_menu.add_command(label="Вставить", command=self.paste)

    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.url_entry.get())

    def paste(self):
        self.url_entry.delete(0, tk.END)
        self.url_entry.insert(0, self.clipboard_get())

    def load_cameras(self):
        cameras = get_cameras_from_db()
        if cameras:
            name, url = cameras[0]  # Загружаем первую камеру для примера
            self.url_entry.delete(0, tk.END)
            self.url_entry.insert(0, url)
            messagebox.showinfo("Камера загружена", f"Камера: {name}, URL: {url}")
        else:
            messagebox.showinfo("Ошибка", "Нет камер в базе данных")

    def start_stream(self):
        url = self.url_entry.get()
        if not url:
            messagebox.showerror("Ошибка", "Введите URL видеопотока")
            return

        self.stop_event.clear()
        self.cap = cv2.VideoCapture(url)

        if not self.cap.isOpened():
            messagebox.showerror("Ошибка", "Не удалось открыть видеопоток")
            print(f"Не удалось открыть видеопоток по URL: {url}")
            return

        self.update_frame()

    def update_frame(self):
        if self.stop_event.is_set():
            return

        ret, frame = self.cap.read()
        if not ret:
            messagebox.showerror("Ошибка", "Не удалось получить кадр")
            print("Не удалось получить кадр")
            return

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(image=img)

        self.video_label.imgtk = imgtk
        self.video_label.configure(image=imgtk)

        self.after(10, self.update_frame)

    def on_close(self):
        self.stop_event.set()
        if self.cap:
            self.cap.release()
        self.destroy()

if __name__ == "__main__":
    app = VideoApp()
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
