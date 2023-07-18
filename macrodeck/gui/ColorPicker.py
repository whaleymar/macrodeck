import math
import sys
import tkinter
from functools import partial

import customtkinter as ctk
from PIL import Image, ImageTk

from macrodeck.gui.util import hovercolor

if sys.platform.startswith("win"):
    import ctypes

    ctypes.windll.shcore.SetProcessDpiAwareness(0)

HEIGHT = 450
WIDTH = 500


class AskColor(ctk.CTkToplevel):
    def __init__(self, used_colors, color=(255, 255, 255)):
        super().__init__()

        self.title("Choose Color")
        self.maxsize(WIDTH, HEIGHT)
        self.minsize(WIDTH, HEIGHT)
        self.attributes("-topmost", True)
        self.lift()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.after(10)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.default_color = [color[0], color[1], color[2]]
        self.rgb_color = self.default_color[:]
        default_color_hex = "#%02x%02x%02x" % color

        self.frame = ctk.CTkFrame(master=self)
        self.frame.grid(row=0, column=0, padx=20, pady=20, sticky="")

        self.used_colors = list(used_colors)
        self.sframe = ctk.CTkScrollableFrame(master=self, width=150)
        self.sframe.grid(row=0, column=1, padx=20, pady=20, sticky="nse")
        self.used_buttons()

        self.canvas = tkinter.Canvas(
            self.frame,
            height=200,
            width=200,
            highlightthickness=0,
            bg=self.frame._apply_appearance_mode(self.frame._fg_color),
        )
        self.canvas.pack(pady=20)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<Button-1>", self.on_mouse_click)

        self.img1 = Image.open("assets/color_wheel.png").resize(
            (200, 200), Image.Resampling.LANCZOS
        )
        self.img2 = Image.open("assets/target.png").resize(
            (20, 20), Image.Resampling.LANCZOS
        )

        self.wheel = ImageTk.PhotoImage(self.img1)
        self.target = ImageTk.PhotoImage(self.img2)

        self.canvas.create_image(100, 100, image=self.wheel)
        self.canvas.create_image(100, 100, image=self.target)

        self.brightness_slider_value = ctk.IntVar()
        self.brightness_slider_value.set(255)

        self.slider = ctk.CTkSlider(
            master=self.frame,
            height=20,
            border_width=1,
            button_length=15,
            progress_color=default_color_hex,
            from_=0,
            to=255,
            variable=self.brightness_slider_value,
            number_of_steps=256,
            command=lambda x: self.update_colors(),
        )
        self.slider.pack(fill="both", pady=(0, 15), padx=20)

        self.label = ctk.CTkLabel(
            master=self.frame,
            text_color="#ffffff",
            height=50,
            fg_color=default_color_hex,
            corner_radius=24,
            text=default_color_hex,
            font=ctk.CTkFont(family="Arial", weight="bold", size=14),
        )
        self.label.pack(fill="both", padx=10)

        self.button = ctk.CTkButton(
            master=self.frame,
            text="OK",
            height=50,
            corner_radius=24,
            command=self._ok_event,
        )
        self.button.pack(fill="both", padx=10, pady=20)

        self.after(150, lambda: self.label.focus())

        self.grab_set()

    def get(self):
        self._color = self.label._fg_color
        self.master.wait_window(self)
        return self._color

    def _ok_event(self, event=None):
        self._color = self.label._fg_color
        self.grab_release()
        self.destroy()

    def _on_closing(self):
        self._color = None
        self.grab_release()
        self.destroy()

    def used_buttons(self):
        for i, color in enumerate(self.used_colors):
            newbutton = ctk.CTkButton(
                master=self.sframe,
                text=color,
                fg_color=color,
                hover_color=hovercolor(color),
                border_width=0,
                corner_radius=0,
                command=partial(self.set_color, i),
            )
            newbutton.grid(row=i, column=0, sticky="ew")

    def set_color(self, i):
        self.label.configure(fg_color=self.used_colors[i])
        self.label.configure(text=self.used_colors[i])
        self.slider.configure(progress_color=self.used_colors[i])

    def on_mouse_drag(self, event):
        x = event.x
        y = event.y
        self.canvas.delete("all")
        self.canvas.create_image(100, 100, image=self.wheel)

        d_from_center = math.sqrt((100 - x) ** 2 + (100 - y) ** 2)

        if d_from_center < 100:
            self.target_x, self.target_y = x, y
        else:
            self.target_x, self.target_y = self.projection_on_circle(x, y, 100, 100, 99)

        self.canvas.create_image(self.target_x, self.target_y, image=self.target)

        self.get_target_color()
        self.update_colors()

    def on_mouse_click(self, event):
        x = event.x
        y = event.y
        self.canvas.delete("all")
        self.canvas.create_image(100, 100, image=self.wheel)

        d_from_center = math.sqrt((100 - x) ** 2 + (100 - y) ** 2)

        if d_from_center < 100:
            self.target_x, self.target_y = x, y
        else:
            self.target_x, self.target_y = self.projection_on_circle(x, y, 100, 100, 99)

        self.canvas.create_image(self.target_x, self.target_y, image=self.target)

        self.get_target_color()
        self.update_colors()

    def get_target_color(self):
        try:
            self.rgb_color = self.img1.getpixel((self.target_x, self.target_y))

            r = self.rgb_color[0]
            g = self.rgb_color[1]
            b = self.rgb_color[2]
            self.rgb_color = [r, g, b]
        except AttributeError:
            self.rgb_color = self.default_color

    def update_colors(self):
        brightness = self.brightness_slider_value.get()

        self.get_target_color()

        r = int(self.rgb_color[0] * (brightness / 255))
        g = int(self.rgb_color[1] * (brightness / 255))
        b = int(self.rgb_color[2] * (brightness / 255))

        self.rgb_color = [r, g, b]

        self.hex_color = "#{:02x}{:02x}{:02x}".format(*self.rgb_color)

        self.slider.configure(progress_color=self.hex_color)
        self.label.configure(fg_color=self.hex_color)

        self.label.configure(text=str(self.hex_color))

        # if self.brightness_slider_value.get() < 70:
        #     self.label.configure(text_color="white")
        # else:
        #     self.label.configure(text_color="black")

        if str(self.label._fg_color) == "black":
            self.label.configure(text_color="white")

    def projection_on_circle(self, point_x, point_y, circle_x, circle_y, radius):
        angle = math.atan2(point_y - circle_y, point_x - circle_x)
        projection_x = circle_x + radius * math.cos(angle)
        projection_y = circle_y + radius * math.sin(angle)

        return projection_x, projection_y
