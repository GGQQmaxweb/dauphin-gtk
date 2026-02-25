#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")

from gi.repository import Gtk, Adw
import urllib.request
import json
import os
import sqlite3

Adw.init()
API_KEY = os.getenv("StuKey")
API_URL = f"https://ilifeapi.az.tku.edu.tw/api/ilifeStuClassApi?q="

class StudentApp(Adw.Application):

    def __init__(self):
        super().__init__(application_id="com.example.StudentApp")
        self.api_data = {"stuelelist": []}

    def do_activate(self):
        self.window = Adw.ApplicationWindow(application=self)
        self.window.set_title("Student Class Viewer")
        self.window.set_default_size(700, 400)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.set_vexpand(True)
        main_box.set_hexpand(True)
        self.window.set_content(main_box)

        # --- Weekday Buttons ---
        self.selected_week = "1"

        weekday_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        weekday_box.set_hexpand(True)
        main_box.append(weekday_box)

        self.week_buttons = {}

        days = [
            ("1", "Mon"),
            ("2", "Tue"),
            ("3", "Wed"),
            ("4", "Thu"),
            ("5", "Fri"),
            ("6", "Sat"),
        ]

        for week_value, label in days:
            button = Gtk.Button(label=label)
            button.connect("clicked", self.on_week_button_clicked, week_value)
            weekday_box.append(button)

            self.week_buttons[week_value] = button

        # Highlight Monday initially
        self.update_week_button_style()

        # --- Bottom Layout ---
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        main_box.append(bottom_box)

        
        # --- Scrollable Class List ---
        self.scrolled = Gtk.ScrolledWindow()
        self.scrolled.set_vexpand(True)
        main_box.append(self.scrolled)

        self.class_list_box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=8
        )

        self.scrolled.set_child(self.class_list_box)
        # --- Info Area ---
        self.info_label = Gtk.Label()
        self.info_label.set_wrap(True)
        bottom_box.append(self.info_label)
        
        self.init_db()

        self.fetch_api()

        self.window.present()

    # -------------------------
    # API Fetch
    # -------------------------
    def fetch_api(self):
        try:
            with urllib.request.urlopen(API_URL) as response:
                data = response.read()
                self.api_data = json.loads(data.decode())

                self.save_to_db(self.api_data["stuelelist"])

        except Exception as e:
            print("API Error:", e)

        self.load_from_db()

    # -------------------------
    # Filter classes
    # -------------------------
    def update_class_list(self):
        # Clear existing items
        while self.class_list_box.get_first_child():
            self.class_list_box.remove(
                self.class_list_box.get_first_child()
            )

        self.filtered = [
            c for c in self.api_data["stuelelist"]
            if c.get("week") == self.selected_week
        ]

        if not self.filtered:
            label = Gtk.Label(label="No classes this day.")
            self.class_list_box.append(label)
            return

        for c in self.filtered:
            card = self.create_class_card(c)
            self.class_list_box.append(card)

    # -------------------------

    def on_week_button_clicked(self, button, week_value):
        self.selected_week = week_value
        self.update_week_button_style()
        self.update_class_list()


    def update_week_button_style(self):
        for week_value, button in self.week_buttons.items():
            if week_value == self.selected_week:
                button.add_css_class("suggested-action")
            else:
                button.remove_css_class("suggested-action")
    
    def create_class_card(self, c):
        periodToTimeTable = {"01": "8:00", "02": "9:00", "03": "10:00", "04": "11:00", "05": "12:00", "06": "13:00", "07": "14:00", "08": "15:00", "09": "16:00", "10": "17:00", "11": "18:00", "12": "19:00", "13": "20:00", "14": "21:00", "15": "22:00", "16": "23:00"}
        frame = Gtk.Frame()
        frame.set_margin_top(6)
        frame.set_margin_bottom(6)
        frame.set_margin_start(6)
        frame.set_margin_end(6)

        box = Gtk.Box(
            orientation=Gtk.Orientation.VERTICAL,
            spacing=4
        )
        box.set_margin_top(10)
        box.set_margin_bottom(10)
        box.set_margin_start(10)
        box.set_margin_end(10)

        title = Gtk.Label()
        title.set_markup(f"<b>{c.get('ch_cos_name')}</b>")
        title.set_xalign(0)

        period = Gtk.Label(
            label=f"Period: {', '.join(c.get('timePlase', {}).get('sesses', []))}"
        )
        period.set_xalign(0)

        time = Gtk.Label(
            label=f"Time: {', '.join([periodToTimeTable.get(s, s) for s in c.get('timePlase', {}).get('sesses', [])])}"
        )
        time.set_xalign(0)

        teacher = Gtk.Label(
            label=f"Teacher: {c.get('teach_name')}"
        )
        teacher.set_xalign(0)

        room = Gtk.Label(
            label=f"Room: {c.get('room')}"
        )
        room.set_xalign(0)

        box.append(title)
        box.append(period)
        box.append(time)
        box.append(teacher)
        box.append(room)
        

        frame.set_child(box)

        return frame

    def init_db(self):
        data_dir = os.path.join(
            os.path.expanduser("~"),
            ".local",
            "share",
            "studentapp"
        )
        os.makedirs(data_dir, exist_ok=True)

        self.db_path = os.path.join(data_dir, "student.db")
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS classes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    week TEXT,
                    ch_name TEXT,
                    en_name TEXT,
                    teacher TEXT,
                    room TEXT,
                    sessions TEXT
                )
            """)
        self.conn.commit()

    import json

    def save_to_db(self, class_list):
        self.cursor.execute("DELETE FROM classes")

        for c in class_list:
            sessions = json.dumps(
                c.get("timePlase", {}).get("sesses", [])
            )

            self.cursor.execute("""
                INSERT INTO classes
                (week, ch_name, en_name, teacher, room, sessions)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                c.get("week"),
                c.get("ch_cos_name"),
                c.get("en_cos_name"),
                c.get("teach_name"),
                c.get("room"),
                sessions
            ))

        self.conn.commit()

    def load_from_db(self):
        self.cursor.execute("""
            SELECT ch_name, en_name, teacher, room, sessions
            FROM classes
            WHERE week=?
        """, (self.selected_week,))

        rows = self.cursor.fetchall()

        while self.class_list_box.get_first_child():
            self.class_list_box.remove(
                self.class_list_box.get_first_child()
            )

        if not rows:
            self.class_list_box.append(
                Gtk.Label(label="No classes this day.")
            )
            return

        for row in rows:
            sessions = json.loads(row[4]) if row[4] else []

            c = {
                "ch_cos_name": row[0],
                "en_cos_name": row[1],
                "teach_name": row[2],
                "room": row[3],
                "timePlase": {
                    "sesses": sessions
                }
            }

            self.class_list_box.append(
                self.create_class_card(c)
            )
        


app = StudentApp()
app.run()