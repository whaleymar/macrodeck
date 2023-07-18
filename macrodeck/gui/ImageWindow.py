import tkinter as tk
from functools import partial

import customtkinter as ctk

from macrodeck.gui.style import BC_DEFAULT, FC_EMPTY, ICON_SIZE
from macrodeck.gui.util import ctkimage, hovercolor

HC_EMPTY = hovercolor(FC_EMPTY)


# popup window for configuring button image
class ImageWindow(ctk.CTkToplevel):
    def __init__(self, images, STANDARDFONT):
        super().__init__()

        imgs_per_row = 4

        WIDTH = 250
        HEIGHT = 300
        self.geometry(f"{WIDTH}x{HEIGHT}")

        self.title("Choose Image")
        self.lift()
        self.after(10)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        self.frame = ctk.CTkFrame(master=self)
        self.frame.grid(padx=5, pady=5, sticky="nswe")

        self.sframe = ctk.CTkScrollableFrame(master=self.frame)
        self.sframe.grid(row=0, column=0, sticky="nsew")

        self.images = [img for img in images if img is not None]
        self.current_image = 0

        self.buttons = []
        for i, img in enumerate(self.images):
            button = ctk.CTkButton(
                master=self.sframe,
                width=32,
                height=32,
                fg_color=FC_EMPTY,
                hover_color=HC_EMPTY,
                border_color=BC_DEFAULT,
                command=partial(self.button_callback, i),
                image=img,
                text="",
            )
            x = i % imgs_per_row
            y = int(i / imgs_per_row)
            button.grid(row=y, column=x, padx=5, pady=5, sticky="nsew")
            self.buttons.append(button)

        self.newimg = ctk.CTkButton(
            master=self.frame, text="New Image", command=self.new_img
        )
        self.newimg.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        self.button = ctk.CTkButton(
            master=self.frame, text="OK", command=self._ok_event
        )
        self.button.grid(row=2, column=0, padx=5, pady=5, sticky="nsew")

        self.grab_set()

    def button_callback(self, ix):
        # print('pressed button', ix)
        self.current_image = ix
        self._ok_event()

    def new_img(self):
        filetypes = (("PNG files", "*.png"), ("All Files", "*.*"))

        f = tk.filedialog.askopenfilename(title="Choose image", filetypes=filetypes)

        if f:
            newimg = ctkimage(f, ICON_SIZE)
            self.current_image = len(self.images)
            self.images.append(newimg)
            self._ok_event()

    def get(self):
        self._img = None
        self.master.wait_window(self)
        return self._img

    def _ok_event(self, event=None):
        self._img = self.images[self.current_image]
        self.grab_release()
        self.destroy()

    def _on_closing(self):
        self._img = None
        self.grab_release()
        self.destroy()
