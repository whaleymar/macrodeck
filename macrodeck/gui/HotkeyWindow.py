import customtkinter as ctk
from macrodeck import KeyCategories

# popup window for configuring hotkeys
class HotkeyWindow(ctk.CTkToplevel):
    def __init__(self, key, modifier, STANDARDFONT):
        super().__init__()
        WIDTH = 350
        HEIGHT=250
        self.geometry(f'{WIDTH}x{HEIGHT}')
        
        self.title("Choose HotKey")
        self.maxsize(WIDTH, HEIGHT)
        self.minsize(WIDTH, HEIGHT)
        self.attributes("-topmost", True)
        self.lift()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.after(10)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.frame = ctk.CTkFrame(master=self)
        self.frame.grid(padx=20, pady=20, sticky="nswe")

        # modifier keys option:
        self.modifier = ctk.CTkOptionMenu(master=self.frame,
                                          values=KeyCategories.MODIFIERKEYSHOTKEY,
                                          font=STANDARDFONT)
        self.modifier.set(modifier[:-1] if modifier !="" else KeyCategories.MODIFIERKEYSHOTKEY[0]) # we store "" instead of "none"
        
        # key: 
        self.key = ctk.CTkOptionMenu(master=self.frame,
                                     values=KeyCategories.NUMPADKEYS+KeyCategories.FUNCTIONKEYS,
                                     font=STANDARDFONT)
        self.key.set(key)

        self.mlabel = ctk.CTkLabel(master=self.frame,text='Modifier Key: ',
                                   font=STANDARDFONT)
        self.klabel = ctk.CTkLabel(master=self.frame,text='Main Key: ',
                                   font=STANDARDFONT)
        
        self.button = ctk.CTkButton(master=self.frame, text="OK", command=self._ok_event)
        
        self.mlabel.grid(row=0, column=0, padx=20, pady=20, sticky='nsw')
        self.klabel.grid(row=1, column=0, padx=20, pady=20, sticky='nsw')
        self.modifier.grid(row=0, column=1, padx=20, pady=20, sticky='nse')
        self.key.grid(row=1, column=1, padx=20, pady=20, sticky='nse')
        self.button.grid(row=2, column=0, columnspan=2, padx=20, pady=20, sticky='nsew')
        
        self.grab_set()

    def get(self):
        self._hotkey = None
        self.master.wait_window(self)
        return self._hotkey
    
    def _ok_event(self, event=None):
        self._hotkey = self.modifier.get(), self.key.get()
        self.grab_release()
        self.destroy()

    def _on_closing(self):
        self._hotkey = None
        self.grab_release()
        self.destroy()