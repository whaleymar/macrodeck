import macrodeck.Keyboard as Keyboard
import macrodeck.KeyCategories as KeyCategories
from macrodeck.VLCPlayer import VLCPlayer
from macrodeck.gui.MacroWindow import MacroWindow
from macrodeck.gui.style import FC_DEFAULT, XPAD, YPAD, ICON_SIZE, ICON_SIZE_WIDE
from macrodeck.gui.util import hovercolor, ctkimage
import tkinter as tk
import customtkinter as ctk
from functools import partial
import webbrowser

FLEX_WIDGET_ROW = 2
FLEX_WIDGET_COL = 1
FLEX_WIDGET_COLSPAN = 2

player = VLCPlayer() # not sure how to avoid this global while having it shared between instances of different classes

class Action(): # lawsuit?
    def __init__(self, name, default_arg, icon, default_text=None, requires_arg=False):
        self.name = name
        self.default_arg = default_arg
        self.default_text = default_text
        self.icon = icon
        self.requires_arg = requires_arg
        self.enum = None

    def display_widget(self, app):
        self._widget(app)

    def _widget(self, app):
        app.destroy_flex()

    def set_enum(self, ix):
        self.enum = ix

    def set_action(self, button):
        """
        set button action enum, default text, and default arg
        """
        button.set_action(self.enum)
        
        if self.default_text is not None: 
            button.set_text(self.default_text, default=True)

        button.set_arg(self.default_arg)

    # action call
    def __call__(self):
        pass

class NoAction(Action):
    def __init__(self):
        super().__init__("No Action", None, None)
        self.player = player

    def __call__(self, app):
        pass

class PlayMedia(Action):
    def __init__(self):
        super().__init__("Play Media", None, ctkimage('assets/action_audio.png', ICON_SIZE_WIDE), requires_arg=True)
        self.player = player

    def _widget(self, app):
        """
        sets flex button to "media chooser" button
        """

        app.destroy_flex()

        filetypes = (
            ('MP3 files', '*.mp3'),
            ('All Files', '*.*')
        )

        button = ctk.CTkButton(app.bottomframe, 
                                command=partial(app.selectfile, filetypes), 
                                text='Choose File',
                                fg_color=FC_DEFAULT,
                                hover_color=hovercolor(FC_DEFAULT),
                                font=app.STANDARDFONT)
        button.grid(row=FLEX_WIDGET_ROW, column=FLEX_WIDGET_COL, columnspan = FLEX_WIDGET_COLSPAN, padx=XPAD, pady=YPAD, sticky='nsew')

        app.flex_button = button

    def __call__(self, path, app):
        self.player(path)

class PauseMedia(Action):
    def __init__(self):
        super().__init__("Pause Media", None, ctkimage('assets/action_pause.png', ICON_SIZE), default_text="Pause Media")
        self.player = player

    def __call__(self, app):
        self.player.toggle_pause()

class StopMedia(Action):
    def __init__(self):
        super().__init__("Stop Media", None, ctkimage('assets/action_mute.png', ICON_SIZE), default_text="Stop Media")
        self.player = player
    
    def __call__(self, app):
        self.player.reset()

class OpenView(Action):
    def __init__(self):
        super().__init__("Open View", None, ctkimage('assets/action_openview.png', ICON_SIZE), requires_arg=True)

    def _widget(self, app):
        """
        sets flex button to drop down widget containing all views
        """

        app.destroy_flex()
        views = [str(l) for l in app.views]

        button_view = ctk.CTkOptionMenu(app.bottomframe,
                                command=app.arg_from_dropdown, 
                                values=views,
                                fg_color=FC_DEFAULT,
                                button_hover_color=hovercolor(FC_DEFAULT),
                                font=app.STANDARDFONT)
        
        button_view.set(str(app.views[app.current_button.arg]))

        # set button default text
        if app.current_button is not app.buttons[app.back_button] or app.views[app.current_view].ismain():
            app.arg_from_dropdown(button_view.get())

        button_view.grid(row=FLEX_WIDGET_ROW, column=FLEX_WIDGET_COL, columnspan = FLEX_WIDGET_COLSPAN, padx=XPAD, pady=YPAD, sticky='nsew')

        app.flex_button = button_view

    def __call__(self, view_enum, app):
        """
        Button Action: tells mainloop to run App.switch_view
        keyboard listener must use this callback
        """

        app.view_enum = view_enum
        app.after(0, app.switch_view)

class Macro(Action):
    def __init__(self):
        super().__init__("Run Macro", None, ctkimage('assets/action_macro.png', ICON_SIZE), requires_arg=True)
        self.keyboard = Keyboard.keyboard()

    def _widget(self, app):
        """
        sets flex button to "macro config" button
        """

        app.destroy_flex()

        button = ctk.CTkButton(app.bottomframe, 
                                command=partial(self.macroconfig, app),
                                text='Set Macro',
                                fg_color=FC_DEFAULT,
                                hover_color=hovercolor(FC_DEFAULT),
                                font=app.STANDARDFONT)
        button.grid(row=FLEX_WIDGET_ROW, column=FLEX_WIDGET_COL, columnspan = FLEX_WIDGET_COLSPAN, padx=XPAD, pady=YPAD, sticky='nsew')

        app.flex_button = button

    def __call__(self, keyset, app):
        self.schedule_macro(keyset, app)

    def macroconfig(self, app):
        """
        Opens MacroWindow instance and changes button's macro once closed
        """

        app.helpertxt_clear()
        if app.current_button is None:
            app.helpertxt_nobtn()
            return

        win = MacroWindow(app.current_button.arg, app.STANDARDFONT)
        newmacro = win.get()
        if newmacro is None:
            return
        
        # convert modifiers with map
        for i in range(len(newmacro)):
            if newmacro[i][0]=='':continue
            newmacro[i] = ("+".join([KeyCategories.MODIFIER_TO_VK[key] for key in newmacro[i][0].split('+')]), newmacro[i][1])

        app.current_button.set_arg(newmacro)

    def schedule_macro(self, keyset, app):
        """
        tells mainloop to run App.run_macro, then kills hotkeys
        """

        self.to_press = keyset
        app.after(100, self.run_macro)
        app.kill_hotkeys()
        app.after_idle(app.init_hotkeys)

    def run_macro(self):
        """
        runs the scheduled macro, then restarts hotkeys
        """

        if self.to_press is None:
            return
        
        for keys in self.to_press:
            keys = [key for key in keys if len(key)>0] # remove empty modifier
            keys = [Keyboard.to_pynput(key) for seq in keys for key in seq.split('+')] # split modifier and flatten
            self.keyboard.press_keys(keys) # send keypress

        self.to_press = None

class Web(Action):
    def __init__(self):
        super().__init__("Open Web Page", "", ctkimage('assets/action_web.png', ICON_SIZE), requires_arg=True)

    def _widget(self, app):
        """
        Sets flex button to text entry widget for URL
        """

        app.destroy_flex()

        app.flex_text = tk.StringVar(app.bottomframe, value='')
        app.flex_text.trace('w',app.arg_from_text) # sets URL argument

        entry = ctk.CTkEntry(app.bottomframe, textvariable=app.flex_text)
        entry.grid(row=FLEX_WIDGET_ROW, column=FLEX_WIDGET_COL, columnspan = FLEX_WIDGET_COLSPAN, padx=XPAD, pady=YPAD, sticky='nsew')
        app.flex_button = entry

    def __call__(self, url, app):
        webbrowser.open(url)