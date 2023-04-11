import tkinter as tk
import customtkinter as ctk
from macrodeck.gui.style import FC_EMPTY
from functools import partial
from macrodeck import KeyCategories

XPAD = 5
YPAD = 5

class MacroWindow(ctk.CTkToplevel):
    def __init__(self, current_macros, font):
        super().__init__()
        WIDTH = 550
        HEIGHT=450
        self.geometry(f'{WIDTH}x{HEIGHT}')
        
        self.title("Choose Macro")
        self.maxsize(WIDTH, HEIGHT)
        self.minsize(WIDTH, HEIGHT)
        self.attributes("-topmost", True)
        self.lift()
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self.after(10)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.frame = ctk.CTkFrame(master=self)
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid(sticky="nsew")

        self.sframe = ctk.CTkScrollableFrame(master = self.frame, width=WIDTH, height=HEIGHT)
        self.sframe.grid_columnconfigure(0, weight=1)
        self.sframe.grid_columnconfigure(1, weight=1)
        self.sframe.grid_rowconfigure(0, weight=1)
        self.sframe.grid(row=0, column=0, sticky='', padx=XPAD, pady=YPAD)

        self.row = 0
        self.font = font

        self._modifiers = []
        self._keys = []
        self._deletebuttons = []
        self._newbuttons = []

        # topmost new button (nothing else goes in this row)
        self._newtopbutton = ctk.CTkButton(master = self.sframe, 
                                                 width=32,
                                                 text="+",
                                                 font=self.font,
                                                 command = partial(self.new_row, None, None, 0))
        self._newtopbutton.grid(row=0, column=2, padx=XPAD, pady=YPAD, sticky='nse')

        # add rows
        if current_macros is None:
            self.new_row()
        else:
            for modifier,key in current_macros:
                self.new_row(modifier = modifier.replace("MENU","ALT").replace("LWIN","WIN"), key=key)
        
        self.okbutton = ctk.CTkButton(master=self.frame, text="OK", command=self._ok_event)
        self.okbutton.grid(row=1, column=0, sticky='',  padx=XPAD, pady=YPAD)
        
        self.grab_set()

    def new_row(self, modifier = None, key = None, ix=None):
        if ix is None:
            ix = self.row

        # modifier keys option:
        self._modifiers.insert(ix, ctk.CTkOptionMenu(master=self.sframe,
                                          values=KeyCategories.MODIFIERKEYSMACRO,
                                          font=self.font))
        self._modifiers[ix].set(KeyCategories.MODIFIERKEYSMACRO[0] if modifier is None else modifier)
        
        # key: 
        self._keys.insert(ix, ctk.CTkOptionMenu(master=self.sframe,
                                    values=[''],
                                    font=self.font))
        
        # create sub-menus for key categories:
        def subKeyMenu(name, keys):
            newKeyMenu = tk.Menu(master = self._keys[ix]._dropdown_menu, 
                                 tearoff=0,
                                 fg='white',
                                 background=FC_EMPTY,
                                 activebackground='gray30',
                                 bd=1,
                                 relief=None)
            for _key in keys:
                newKeyMenu.add_command(label=_key, command=partial(self._keys[ix].set, _key))
            self._keys[ix]._dropdown_menu.add_cascade(label=name, menu=newKeyMenu)

        subKeyMenu('Alphanumeric', KeyCategories.ALPHANUMERICKEYS)
        subKeyMenu('Numpad', KeyCategories.NUMPADKEYS)
        subKeyMenu('Function', KeyCategories.FUNCTIONKEYS)
        # subKeyMenu('System', key_categories.SYSTEMKEYS) # not working
        subKeyMenu('Misc', KeyCategories.MISCKEYS)
        # subKeyMenu('Mouse', key_categories.MOUSEKEYS) # not working 
        subKeyMenu('Media', KeyCategories.MEDIAKEYS)

        self._keys[ix].set('' if key is None else key)

        # new delete button:
        self._deletebuttons.append(ctk.CTkButton(master = self.sframe, 
                                                 width=32,
                                                 text="X",
                                                 font=self.font,
                                                 command = partial(self.delete_row, self.row)))
        
        # new new button
        self._newbuttons.append(ctk.CTkButton(master = self.sframe, 
                                                 width=32,
                                                 text="+",
                                                 font=self.font,
                                                 command = partial(self.new_row, None, None, self.row+1)))
        
        # place new/delete buttons on last row
        self._deletebuttons[self.row].grid(row=self.row+1, column=3, padx=XPAD, pady=YPAD, sticky='nse')
        self._newbuttons[self.row].grid(row=self.row+1, column=2, padx=XPAD, pady=YPAD, sticky='nse')

        self.row+=1

        # move drop down menus down
        for i in range(ix, len(self._modifiers)):
            self._modifiers[i].grid(row=i+1, column=0, padx=XPAD, pady=YPAD, sticky='nsew')
            self._keys[i].grid(row=i+1, column=1, padx=XPAD, pady=YPAD, sticky='nsew')

    def delete_row(self, ix):
        self._modifiers[ix].destroy()
        self._keys[ix].destroy()
        self._modifiers.pop(ix)
        self._keys.pop(ix)

        # remove last delete button
        self._deletebuttons[-1].destroy()
        self._deletebuttons.pop()

        # remove last new button
        self._newbuttons[-1].destroy()
        self._newbuttons.pop()

        self.row-=1

        if len(self._modifiers) == ix:
            return
        
        # move lower buttons up
        for i in range(ix, len(self._modifiers)):
            self._modifiers[i].grid(row=i+1, column=0, padx=XPAD, pady=YPAD, sticky='nsew')
            self._keys[i].grid(row=i+1, column=1, padx=XPAD, pady=YPAD, sticky='nsew')

    def get(self):
        self._macro = None
        self.master.wait_window(self)
        return self._macro
    
    def _ok_event(self, event=None):
        self._macro = [(modifier.get(), key.get()) for modifier, key in zip(self._modifiers, self._keys) if (len(key.get())>0 or len(modifier.get())>0)]
        self.grab_release()
        self.destroy()

    def _on_closing(self):
        self._macro = None
        self.grab_release()
        self.destroy()