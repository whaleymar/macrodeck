import macrodeck.Keyboard as Keyboard
import macrodeck.KeyCategories as KeyCategories
from macrodeck.gui.style import FC_DEFAULT, FC_DEFAULT2, FC_EMPTY, BC_DEFAULT, XPAD, YPAD, ICON_SIZE, ICON_SIZE_WIDE
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
    def __init__(self, name, default_arg, icon, default_text=None, requires_arg=False, inactive=False, calls_after=False):
        self.name = name
        self.default_arg = default_arg
        self.default_text = default_text
        self.icon = icon
        self.requires_arg = requires_arg
        self._inactive = inactive # if true, this action does nothing and will make the button grayed-out
        self.enum = None
        self.calls_after = calls_after

    def display_widget(self, app, changed):
        app.destroy_flex()
        widget1, widget2 = self._widget(app, app.bottomframe, changed)

        colspan = FLEX_WIDGET_COLSPAN if widget2 is None else FLEX_WIDGET_COLSPAN//2
        if widget1 is not None:
            widget1.grid(row=FLEX_WIDGET_ROW, column=FLEX_WIDGET_COL, columnspan = colspan, padx=XPAD, pady=YPAD, sticky='nsew')
            app.flex_button = widget1
        if widget2 is not None:
            widget2.grid(row=FLEX_WIDGET_ROW, column=FLEX_WIDGET_COL+1, columnspan = colspan, padx=XPAD, pady=YPAD, sticky='nsew')
            app.flex_button2 = widget2

    def _widget(self, app, frame, changed):
        return (None, None)

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

    def _widget(self, app, frame, changed):
        """
        sets flex button to "media chooser" button
        """

        filetypes = (
            ('MP3 files', '*.mp3'),
            ('All Files', '*.*')
        )

        button = ctk.CTkButton(frame, 
                                command=partial(app.selectfile, filetypes), 
                                text='Choose File',
                                fg_color=FC_DEFAULT,
                                hover_color=hovercolor(FC_DEFAULT),
                                font=app.STANDARDFONT)
        
        return button, None

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
        super().__init__("Open View", 0, ctkimage('assets/action_openview.png', ICON_SIZE), requires_arg=True, calls_after=True)

    def _widget(self, app, frame, changed):
        """
        sets flex button to drop down widget containing all views
        """

        views = [str(l) for l in app.views]

        button_view = ctk.CTkOptionMenu(frame,
                                command=app.view_from_dropdown, 
                                values=views,
                                fg_color=FC_DEFAULT,
                                button_hover_color=hovercolor(FC_DEFAULT),
                                font=app.STANDARDFONT)
        
        button_view.set(str(app.views[app.current_button.arg]))

        # set button default text (except for back buttons)
        if changed and (app.current_button is not app.buttons[app.back_button] or app.views[app.current_view].ismain()):
            app.view_from_dropdown(button_view.get())

        return button_view, None

    def __call__(self, view_enum, app, multi_action=False):
        """
        Button Action: tells mainloop to run App.switch_view
        keyboard listener must use this callback
        """

        app.view_enum = view_enum
        if multi_action:
            app.switch_view()
        else:
            app.after(0, app.switch_view)


class Macro(Action):
    def __init__(self):
        super().__init__("Run Macro", None, ctkimage('assets/action_macro.png', ICON_SIZE), requires_arg=True, calls_after=True)
        self.keyboard = Keyboard.keyboard()

    def _widget(self, app, frame, changed):
        """
        sets flex button to "macro config" button
        """

        if not changed:
            arg = app.current_button.get_arg()
            modifier, key = arg
            modifier = modifier.replace("MENU","ALT").replace("LWIN","WIN")
        else:
            modifier = None
            key = None

        self.modMenu = ctk.CTkOptionMenu(master=frame,
                                    values=KeyCategories.MODIFIERKEYSMACRO,
                                    font=app.STANDARDFONT,
                                    fg_color=FC_DEFAULT,
                                    command=partial(self.macro_config, app, True))
        self.modMenu.set(KeyCategories.MODIFIERKEYSMACRO[0] if modifier is None else modifier)

        self.keyMenu = ctk.CTkOptionMenu(master=frame,
                                    values=[''],
                                    fg_color=FC_DEFAULT,
                                    font=app.STANDARDFONT)

        # create sub-menus for key categories:
        def subKeyMenu(name, keys):
            newKeyMenu = tk.Menu(master = self.keyMenu._dropdown_menu, 
                                 tearoff=0,
                                 fg='white',
                                 background=FC_EMPTY,
                                 activebackground='gray30',
                                 bd=1,
                                 relief=None)
            for _key in keys:
                newKeyMenu.add_command(label=_key, 
                                       command=partial(self.macro_config, app, False, _key)
                                       )
            self.keyMenu._dropdown_menu.add_cascade(label=name, menu=newKeyMenu)

        subKeyMenu('Alphanumeric', KeyCategories.ALPHANUMERICKEYS)
        subKeyMenu('Numpad', KeyCategories.NUMPADKEYS)
        subKeyMenu('Function', KeyCategories.FUNCTIONKEYS)
        # subKeyMenu('System', key_categories.SYSTEMKEYS) # not working
        subKeyMenu('Misc', KeyCategories.MISCKEYS)
        # subKeyMenu('Mouse', key_categories.MOUSEKEYS) # not working 
        subKeyMenu('Media', KeyCategories.MEDIAKEYS)

        self.keyMenu.set('' if key is None else key)

        return self.modMenu, self.keyMenu

    def __call__(self, keyset, app, multi_action=False):
        """
        runs macro within tk mainloop
        """

        self.to_press = keyset

        if multi_action:
            # already in mainloop
            self.run_macro()
        else:
            # tells mainloop to run App.run_macro, then kills hotkeys
            app.after(100, self.run_macro)
            app.kill_hotkeys()
            app.after_idle(app.init_hotkeys)

    def macro_config(self, app, is_modifier, _key):
        """
        Updates button arg with new macro
        """
        if is_modifier:
            modifier = _key
            key = self.keyMenu.get()
        else:
            modifier = self.modMenu.get()
            key = _key
            self.keyMenu.set(_key) # have to set here due to nested menu

        if not (len(modifier)>0 or len(key)>0):
            return
        
        modifier = "+".join([KeyCategories.MODIFIER_TO_VK[key] for key in modifier.split('+')])
        
        app.current_button.set_arg((modifier, key))

    def run_macro(self):
        """
        runs the scheduled macro, then restarts hotkeys
        """

        if self.to_press is None:
            return
        
        time.sleep(0.1) # give time for hotkey to be depressed # TODO better way to do this by checking pressed keys?
        keys = [key for key in self.to_press if len(key)>0] # remove empty modifier
        keys = [Keyboard.to_pynput(key) for seq in keys for key in seq.split('+')] # split modifier and flatten
        self.keyboard.press_keys(keys) # send keypress

        self.to_press = None


class Web(Action):
    def __init__(self):
        super().__init__("Open Web Page", "", ctkimage('assets/action_web.png', ICON_SIZE), requires_arg=True)

    def _widget(self, app, frame, changed):
        """
        Sets flex button to text entry widget for URL
        """

        app.flex_text = tk.StringVar(frame, value='')
        app.flex_text.trace('w',app.arg_from_text) # sets URL argument

        entry = ctk.CTkEntry(app.bottomframe, textvariable=app.flex_text)

        # set url in text entry box
        if not changed:
            app.flex_text.set(app.current_button.arg)

        return entry, None

    def __call__(self, url, app):
        webbrowser.open(url)


class OBSScene(Action):
    def __init__(self):
        super().__init__("Open OBS Scene", None, None, requires_arg=True)

    def _widget(self, app, frame, changed):
        """
        sets flex button to drop down widget containing all OBS scenes
        """
        
        # if app.obsws is None: # not working when auto-reconnect is enabled
        try:
            app.obsws.call(requests.GetSceneList())
        except:
            app.helper.configure(text='Could not connect to OBS web server')
            return None, None
        
        scenes = [scene['sceneName'] for scene in app.obsws.call(requests.GetSceneList()).getScenes()]

        button = ctk.CTkOptionMenu(frame,
                                command=app.arg_from_dropdown, 
                                values=scenes,
                                fg_color=FC_DEFAULT,
                                button_hover_color=hovercolor(FC_DEFAULT),
                                font=app.STANDARDFONT)
        
        if not changed:
            button.set(app.current_button.arg)
        else:
            # set button default text
            app.arg_from_dropdown(button.get())

        return button, None

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

    def _widget(self, app, frame, changed):
        """
        sets flex button to drop down widget containing all OBS sources
        """
        
        if app.obsws is None:
            app.helper.configure(text='Could not connect to OBS web server')
            return None, None
        
        sourcelisttemp = app.obsws.call(requests.GetSourcesList())
        sources = [source['sourceName'] for source in app.obsws.call(requests.GetSourcesList()).getSources()]

        button = ctk.CTkOptionMenu(frame,
                                command=app.arg_from_dropdown, 
                                values=sources,
                                fg_color=FC_DEFAULT,
                                button_hover_color=hovercolor(FC_DEFAULT),
                                font=app.STANDARDFONT)
        
        if not changed:
            button.set(app.current_button.arg)
        else:
            # set button default text
            app.arg_from_dropdown(button.get())

        return button, None

    def __call__(self, arg, app):
        if app.obsws is None:
            app.helper.configure(text='Could not connect to OBS web server')
            return
        
        app.obsws.call(requests.GetMute(arg))
        app.obsws.call(requests.SetMute(arg))


class ManageWindow(Action):
    def __init__(self):
        super().__init__("Move/Open Application", None, None, requires_arg=True, calls_after=True)
        self.connection = wmi.WMI()
        self.nameCache = {}

    def _widget(self, app, frame, changed):
        """
        sets flex button to drop down widget containing all window names

        on selection: the current position of the window is saved
        """
        
        windows = self.getVisibleWindows()

        names = self.getAppNames(windows)

        # dropdown containing applications:
        button = ctk.CTkOptionMenu(frame,
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
                                text='Update Position',
                                fg_color=BC_DEFAULT,
                                hover_color=hovercolor(BC_DEFAULT),
                                font=app.STANDARDFONT)

        return button, updatebutton

    def __call__(self, arg, app, multi_action=False):
        if multi_action:
            self.moveWindow(arg)
        else:
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