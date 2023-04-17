import macrodeck.Keyboard as Keyboard
import macrodeck.KeyCategories as KeyCategories
from macrodeck.gui.MacroWindow import MacroWindow
from macrodeck.gui.style import FC_DEFAULT, BC_DEFAULT, XPAD, YPAD, ICON_SIZE, ICON_SIZE_WIDE
from macrodeck.gui.util import hovercolor, ctkimage
import tkinter as tk
import customtkinter as ctk
from functools import partial
import webbrowser
import win32gui
import win32process
import wmi
import os
import time

try:
    from obswebsocket import requests
except ModuleNotFoundError:
    pass

FLEX_WIDGET_ROW = 2
FLEX_WIDGET_COL = 1
FLEX_WIDGET_COLSPAN = 2

class Action(): # lawsuit?
    def __init__(self, name, default_arg, icon, default_text=None, requires_arg=False, inactive=False):
        self.name = name
        self.default_arg = default_arg
        self.default_text = default_text
        self.icon = icon
        self.requires_arg = requires_arg
        self._inactive = inactive # if true, this action does nothing and will make the button grayed-out
        self.enum = None

    def display_widget(self, app, changed):
        self._widget(app, changed)

    def _widget(self, app, changed):
        app.destroy_flex()

    def set_enum(self, ix):
        self.enum = ix

    def inactive(self):
        return self._inactive

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
        super().__init__("No Action", None, None, inactive=True)

    def __call__(self, app):
        pass


class PlayMedia(Action):
    def __init__(self):
        super().__init__("Play Media", None, ctkimage('assets/action_audio.png', ICON_SIZE_WIDE), requires_arg=True)

    def _widget(self, app, changed):
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
        app.player(path)


class PauseMedia(Action):
    def __init__(self):
        super().__init__("Pause Media", None, ctkimage('assets/action_pause.png', ICON_SIZE), default_text="Pause Media")

    def __call__(self, app):
        app.player.toggle_pause()


class StopMedia(Action):
    def __init__(self):
        super().__init__("Stop Media", None, ctkimage('assets/action_mute.png', ICON_SIZE), default_text="Stop Media")
    
    def __call__(self, app):
        app.player.reset()


class OpenView(Action):
    def __init__(self):
        super().__init__("Open View", 0, ctkimage('assets/action_openview.png', ICON_SIZE), requires_arg=True)

    def _widget(self, app, changed):
        """
        sets flex button to drop down widget containing all views
        """

        app.destroy_flex()
        views = [str(l) for l in app.views]

        button_view = ctk.CTkOptionMenu(app.bottomframe,
                                command=app.view_from_dropdown, 
                                values=views,
                                fg_color=FC_DEFAULT,
                                button_hover_color=hovercolor(FC_DEFAULT),
                                font=app.STANDARDFONT)
        
        button_view.set(str(app.views[app.current_button.arg]))

        # set button default text (except for back buttons)
        if app.current_button is not app.buttons[app.back_button] or app.views[app.current_view].ismain():
            app.view_from_dropdown(button_view.get())

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

    def _widget(self, app, changed):
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

    def _widget(self, app, changed):
        """
        Sets flex button to text entry widget for URL
        """

        app.destroy_flex()

        app.flex_text = tk.StringVar(app.bottomframe, value='')
        app.flex_text.trace('w',app.arg_from_text) # sets URL argument

        entry = ctk.CTkEntry(app.bottomframe, textvariable=app.flex_text)
        entry.grid(row=FLEX_WIDGET_ROW, column=FLEX_WIDGET_COL, columnspan = FLEX_WIDGET_COLSPAN, padx=XPAD, pady=YPAD, sticky='nsew')
        app.flex_button = entry

        # set url in text entry box
        if not changed:
            app.flex_text.set(app.current_button.arg)

    def __call__(self, url, app):
        webbrowser.open(url)

class OBSScene(Action):
    def __init__(self):
        super().__init__("Open OBS Scene", None, None, requires_arg=True)

    def _widget(self, app, changed):
        """
        sets flex button to drop down widget containing all OBS scenes
        """
        
        app.destroy_flex()
        # if app.obsws is None: # not working when auto-reconnect is enabled
        try:
            app.obsws.call(requests.GetSceneList())
        except:
            app.helper.configure(text='Could not connect to OBS web server')
            return
        
        scenes = [scene['sceneName'] for scene in app.obsws.call(requests.GetSceneList()).getScenes()]

        button = ctk.CTkOptionMenu(app.bottomframe,
                                command=app.arg_from_dropdown, 
                                values=scenes,
                                fg_color=FC_DEFAULT,
                                button_hover_color=hovercolor(FC_DEFAULT),
                                font=app.STANDARDFONT)
        
        if app.current_button.arg is not None:
            button.set(app.current_button.arg)

        # set button default text
        app.arg_from_dropdown(button.get())

        button.grid(row=FLEX_WIDGET_ROW, column=FLEX_WIDGET_COL, columnspan = FLEX_WIDGET_COLSPAN, padx=XPAD, pady=YPAD, sticky='nsew')

        app.flex_button = button

    def __call__(self, arg, app):
        # if app.obsws is None: # not working when auto-reconnect is enabled
        try:
            app.obsws.call(requests.GetSceneList())
        except:
            app.helper.configure(text='Could not connect to OBS web server')
            return
        
        app.obsws.call(requests.SetCurrentProgramScene(sceneName=arg))

class OBSMute(Action):
    def __init__(self):
        raise NotImplementedError
        super().__init__("Mute OBS Source", None, None, requires_arg=True)

    def _widget(self, app, changed):
        """
        sets flex button to drop down widget containing all OBS sources
        """
        
        app.destroy_flex()
        if app.obsws is None:
            app.helper.configure(text='Could not connect to OBS web server')
            return
        
        sourcelisttemp = app.obsws.call(requests.GetSourcesList())
        sources = [source['sourceName'] for source in app.obsws.call(requests.GetSourcesList()).getSources()]

        button = ctk.CTkOptionMenu(app.bottomframe,
                                command=app.arg_from_dropdown, 
                                values=sources,
                                fg_color=FC_DEFAULT,
                                button_hover_color=hovercolor(FC_DEFAULT),
                                font=app.STANDARDFONT)
        
        if app.current_button.arg is not None:
            button.set(app.current_button.arg)

        # set button default text
        app.arg_from_dropdown(button.get())

        button.grid(row=FLEX_WIDGET_ROW, column=FLEX_WIDGET_COL, columnspan = FLEX_WIDGET_COLSPAN, padx=XPAD, pady=YPAD, sticky='nsew')

        app.flex_button = button

    def __call__(self, arg, app):
        if app.obsws is None:
            app.helper.configure(text='Could not connect to OBS web server')
            return
        
        app.obsws.call(requests.GetMute(arg))
        app.obsws.call(requests.SetMute(arg))


class ManageWindow(Action):
    def __init__(self):
        super().__init__("Move/Open Application", None, None, requires_arg=True)
        self.connection = wmi.WMI()
        self.nameCache = {}

    def _widget(self, app, changed):
        """
        sets flex button to drop down widget containing all window names

        on selection: the current position of the window is saved
        """
        
        app.destroy_flex()
        
        windows = self.getVisibleWindows()

        names = self.getAppNames(windows)

        # dropdown containing applications:
        button = ctk.CTkOptionMenu(app.bottomframe,
                                command=partial(self.saveConfig, app, windows), 
                                values=names,
                                fg_color=FC_DEFAULT,
                                button_hover_color=hovercolor(FC_DEFAULT),
                                dynamic_resizing=False,
                                font=app.STANDARDFONT)
        
        if not changed and app.current_button.arg is not None:
            hwnd = self.appToWindow(app.current_button.arg[0], app.current_button.arg[1])
            if hwnd is not None:
                button.set(win32gui.GetWindowText(hwnd))
            else:
                app.helper.configure(text=f"Could not find window: {os.path.basename(app.current_button.arg[0]) if app.current_button.arg[1] else app.current_button.arg[0]}")

        # setting button args if we changed the action:
        if changed:
            self.saveConfig(app, windows, button.get())

        # button to update coordinates of selected application:
        updatebutton = ctk.CTkButton(app.bottomframe, 
                                command=partial(self.saveConfig, app, windows), 
                                text='Update',
                                fg_color=BC_DEFAULT,
                                hover_color=hovercolor(BC_DEFAULT),
                                font=app.STANDARDFONT)

        button.grid(row=FLEX_WIDGET_ROW, column=FLEX_WIDGET_COL, columnspan = 1, padx=XPAD, pady=YPAD, sticky='nsew')
        updatebutton.grid(row=FLEX_WIDGET_ROW, column=FLEX_WIDGET_COL+1, columnspan = 1, padx=XPAD, pady=YPAD, sticky='nsew')

        app.flex_button = button

    def __call__(self, arg, app):        
        app.after(0, self.moveWindow, arg)

    def moveWindow(self, arg):
        appname, isPath, coords = arg

        hwnd = self.appToWindow(appname, isPath)
        if hwnd is None:
            shouldReturn = True
            # attempt to open the application
            if isPath:
                os.startfile(appname) # doesn't work for apps from the windows app store? vscode python extension bug: anything opened by this line will be closed when the debugger terminates
                time.sleep(1) # give time to open
                
                # re-calc hwnd
                hwnd = self.appToWindow(appname, isPath)
                if hwnd is not None:
                    shouldReturn = False

            if shouldReturn:
                print(f"Could not find window: {os.path.basename(appname) if isPath else appname}")
                return
        
        win32gui.MoveWindow(hwnd, *self.boxToParams(coords), True)

    def appToWindow(self, appname, isPath):
        for hwnd in self.getVisibleWindows():
            if (isPath and self.getAppPath(hwnd)==appname) or (not isPath and win32gui.GetWindowText(hwnd)==appname):
                return hwnd
        return None

    def getAppPath(self, hwnd):
        """
        returns window's executable path
        """
        if hwnd in self.nameCache.keys():
            return self.nameCache[hwnd]
        
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            for p in self.connection.query('SELECT ExecutablePath FROM Win32_Process WHERE ProcessId = %s' % str(pid)):
                exe = p.ExecutablePath
                break
        except:
            result = None
        else:
            result = exe

        self.nameCache[hwnd] = result
        return result
        
    def boxToParams(self, coords):
        left, top, right, bottom = coords
        return left, top, right - left, bottom - top
    
    def getWindow(self, hwnd, result):
        if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
            result.append(hwnd)

    def getVisibleWindows(self):
        """
        loop through all windows and store those that are visible and named
        """
        result = []
        win32gui.EnumWindows(self.getWindow, result)
        return result
    
    def processEXE(self, exeName):
        if exeName is None:
            exeName = "<No .exe found>"
        else:
            exeName = os.path.basename(exeName)

        return exeName
    
    def getAppNames(self, windows):

        result = []
        for hwnd in windows:
            exeName = self.processEXE(self.getAppPath(hwnd))
            result.append(f"{exeName} | {win32gui.GetWindowText(hwnd)}")
        return result
    
    def saveConfig(self, app, windows, winName=None):
        """
        given a window title, saves button arg as a tuple containing (appname, isPath, coords)
        """
        hwnd = None
        if winName is not None:
            # dropdown selection
            for _hwnd in windows:
                exeName = self.processEXE(self.getAppPath(_hwnd))
                if f"{exeName} | {win32gui.GetWindowText(_hwnd)}" == winName:
                    hwnd = _hwnd
                    break
        else:
            # "update" button pressed; use current button args
            hwnd = self.appToWindow(app.current_button.arg[0], app.current_button.arg[1])

        if hwnd is None:
            raise ValueError
        
        coords = win32gui.GetWindowRect(hwnd)

        # appname: exe path if exists, else window title 
        isPath = True
        appname = self.getAppPath(hwnd)
        if appname is None:
            appname = win32gui.GetWindowText(hwnd)
            isPath = False
        app.current_button.set_arg((appname, isPath, coords))