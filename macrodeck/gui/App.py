import tkinter as tk
import customtkinter as ctk
from macrodeck.gui.util import hovercolor, to_rgb, ctkimage, genericSwap, scaling_factor
import os
import macrodeck.Keyboard as Keyboard
from macrodeck import Actions
from macrodeck.gui.ActionButton import ActionButton, HAS_OBSWS
from macrodeck.gui.ButtonView import View, ViewButton
from macrodeck.gui.ColorPicker import (
    AskColor,
)  # from https://github.com/Akascape/CTkColorPicker
from macrodeck.gui.HotkeyWindow import HotkeyWindow
from macrodeck.gui.ImageWindow import ImageWindow
from macrodeck.gui.MultiAction import MultiAction, WRAPLEN_MA
from macrodeck.gui.style import (
    BC_ACTIVE,
    BC_DEFAULT,
    FC_DEFAULT,
    FC_DEFAULT2,
    FC_EMPTY,
    WRAPLEN,
    ICON_SIZE,
    ICON_SIZE_WIDE,
    XPAD,
    YPAD,
)
from functools import partial
import json
from macrodeck.VLCPlayer import VLCPlayer, HAS_VLC
import threading

try:
    from obswebsocket import obsws

    OBS_CONNECTED = True
except ModuleNotFoundError:
    OBS_CONNECTED = False

####################################
# WINDOW APPEARANCE
####################################
scale = scaling_factor()
ctk.set_appearance_mode("System")  # Modes: system (default), light, dark
ctk.set_default_color_theme("dark-blue")  # Themes: blue (default), dark-blue, green
ctk.set_window_scaling(scale)
ctk.set_widget_scaling(scale)

####################################
# CONSTANTS
####################################

# geo
XDIM = 800
YDIM = 800  # 700 good for normal numpad

BUTTON_SIZES = {"regular": (1, 1), "tall": (2, 1), "wide": (1, 2)}

HC_EMPTY = hovercolor(FC_EMPTY)
HC_DEFAULT = hovercolor(FC_DEFAULT)

FLEX_WIDGET_ROW = 2
FLEX_WIDGET_COL = 1
FLEX_WIDGET_COLSPAN = 2

####################################
# ACTIONS
####################################

ACTIONS = Actions.ACTIONS
Actions.add_action(MultiAction())

ACTION_ICONS = [action.icon for action in ACTIONS]
NAME_TO_ACTION = {action.name: action for action in ACTIONS}

# register unique action keys
assert len(ACTIONS) == len(set([action.unique_key() for action in ACTIONS]))
ENUM_TO_UID = {action.enum: action.unique_key() for action in ACTIONS}
UID_TO_ENUM = {v: k for k, v in ENUM_TO_UID.items()}


class App(ctk.CTk):
    def __init__(self, key_layout):
        super().__init__()

        self.geometry(f"{XDIM}x{YDIM}")
        self.iconbitmap("assets/icon.ico")
        self.title("MacroDeck")

        self.STANDARDFONT = ctk.CTkFont(
            family="Arial", weight="bold", size=14
        )  # default size is 13
        self.SMALLFONT = ctk.CTkFont(family="Arial", size=14)  # default size is 13

        # init media player
        if HAS_VLC:
            self.player = VLCPlayer()
        else:
            self.player = None

        # init OBS web socket
        # using a thread so startup isn't slow
        if HAS_OBSWS:
            t = threading.Thread(
                target=self.init_obs_server, daemon=True, name="OBS Web Server"
            )
            t.start()
        else:
            self.obsws = None

        # make all widgets focus-able so I can click out of entry box:
        # also make buttons un-focusable by clicking outside of a widget
        self.bind_all("<1>", lambda event: self.entryconfig(event))

        # init right click menu for views:
        self.rclickmenu = self.createViewMenu()

        # save views on closing:
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        # create menu bar
        self.config(menu=self.createMenuBar())
        self.viewmode = 0  # 0: edit, 1: focused

        ####################################
        # FRAMES
        ####################################

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # BOTTOM (button settings)
        self.bottomframe = ctk.CTkFrame(
            self, width=(XDIM / 2 - XPAD * 2), height=(YDIM - YPAD * 2)
        )
        self.bottomframe.grid(row=1, column=1, sticky="s")
        self.hideEditMenu()

        # LEFT SIDEBAR (view selection)
        self.lframe = ctk.CTkScrollableFrame(self, corner_radius=0, height=YDIM)
        self.lframe.grid(row=0, column=0, rowspan=2, sticky="nsew")
        self.lframe.grid_columnconfigure(0, weight=1)
        self.newviewbutton = ctk.CTkButton(
            self.lframe,
            corner_radius=4,
            height=40,
            border_spacing=10,
            text="New View",
            font=self.STANDARDFONT,
            anchor="w",
            command=self.new_view,
        )
        self.newviewbutton.grid(row=0, column=0, sticky="ew")

        # TOP
        # button grid
        buttonGridXDim = XDIM - XPAD * 2
        buttonGridYDim = YDIM - YPAD * 2
        self.topframe = ctk.CTkFrame(self, width=buttonGridXDim, height=buttonGridYDim)
        self.topframe.grid(row=0, column=1, sticky="n")

        # multi action settings
        self.MAframe = ctk.CTkFrame(self, width=buttonGridXDim, height=buttonGridYDim)
        self.MAframe.grid(row=0, column=1, sticky="n")
        self.MAframe.grid_remove()
        self.MAframe_active = False

        ####################################
        # MISC
        ####################################

        self.text_shared = tk.StringVar(self.bottomframe, value="")
        self.text_shared.trace("w", self.renamebutton)  # callback when text is edited

        self.current_button = None
        self.parent_button = None  # owner of a multi action

        self.initialdir = "/"  # where we start when opening a file
        self.flex_button = None
        self.flex_button2 = None
        self.flex_text = None
        self.global_checkbox = None
        self.to_press = None

        self.key_layout = os.path.basename(key_layout)[
            :-5
        ]  # name of layout file without extension
        self.buttons = self.numpad_buttongrid(key_layout)
        (
            self.helper,
            self.txtbox,
            self.action,
            self.button_clr,
            self.button_hkey,
        ) = self.button_settings()

        # load save:
        try:
            with open("savedata.json", "r") as f:
                savedata = json.load(f)
        except FileNotFoundError:
            savedata = None

        ####################################
        # IMAGES
        ####################################
        if savedata is None:
            self.images = [action.icon for action in ACTIONS if action.icon is not None]
        else:
            try:
                self.load_imgs(savedata)
            except KeyError:
                self.images = [
                    action.icon for action in ACTIONS if action.icon is not None
                ]

        ####################################
        # VIEWS
        ####################################

        # store empty view -- blank slate for new views
        self.empty_view = View("View 1", self.buttons)

        # load views
        self.used_colors = {FC_DEFAULT, FC_DEFAULT2, FC_EMPTY}
        if savedata is None:
            self.views = [self.empty_view]
        else:
            try:
                self.load_views(savedata)
            except KeyError:
                self.views = [self.empty_view]
        self.views[0]._main = True
        self.current_view = 0
        self.refresh_sidebar(True)

        # set global buttons:
        if savedata is not None:
            try:
                self.load_globals(savedata)
            except KeyError:
                pass

    def init_hotkeys(self):
        """
        starts hotkey keyboard listener
        """

        self.hotkeys = Keyboard.init_hotkeys(
            self.buttons
        )  # inherits from threading.thread
        self.hotkeys.start()

    def kill_hotkeys(self):
        """
        stops hotkey keyboard listener
        """

        self.hotkeys.stop()
        self.hotkeys = None

    def spawn_daemon(self, target, name=None):
        """
        spawns daemon thread that runs the function that target points to

        should only be called within mainloop (i think)
        """

        thread = threading.Thread(target=target, args=[self], daemon=True, name=name)
        thread.start()

    def init_obs_server(self):
        """
        init obs web server (if possible)
        """

        print("Attempting to connect to OBS web server")

        if not OBS_CONNECTED:
            self.obsws = None
            return

        try:
            with open("obsserverlogin.txt", "r") as f:
                host, port, password = [elem.strip() for elem in f.readlines()]
        except FileNotFoundError:
            print("File not found: obsserverlogin.txt")
            self.obsws = None
            return

        try:
            self.obsws = obsws(host, int(port), password, authreconnect=30)
            self.obsws.connect()
        except:  # throwing multiple exceptions if OBS is closed, can't seem to catch them all :(
            print("Couldn't connect to OBS web server")
            self.obsws = None
            return

        print("Connected to OBS web server")

    def button_callback(self, button_ix):
        """
        runs when we click a button w/ the mouse
        """

        # run button action if it was already selected
        if self.current_button is self.buttons[button_ix]:
            self.current_button.run_action()
            return

        # reset dynamic vars
        self.reset_bordercols()
        self.helpertxt_clear()
        self.current_button = self.buttons[button_ix]

        # highlight selected button
        self.current_button.configure(border_color=BC_ACTIVE)

        if self.viewmode == 1:
            return

        # set current button details in editor:
        self.text_shared.set(self.current_button.cget("text"))
        b_action = ACTIONS[self.current_button.action_enum].name
        self.action.set(b_action)
        self.set_actionbutton(b_action, False)
        self.showEditMenu()

        if not self.views[self.current_view].ismain():
            return

        if button_ix != self.back_button:
            self.init_global_checkbox()
            if self.current_button._global:
                self.global_checkbox.select()
            else:
                self.global_checkbox.deselect()
        else:
            self.destroy_global_checkbox()

    def button_callback_MA(self):
        """
        runs when we click a multi action button (within self.MAframe)

        shows button editor for the sub-action button
        """

        self.text_shared.set(self.current_button.cget("text"))
        b_action = ACTIONS[self.current_button.action_enum].name
        self.action.set(b_action)
        self.set_actionbutton(b_action, False)
        self.showEditMenu()

        self.destroy_global_checkbox()

    def hideEditMenu(self):
        """
        hides bottom frame (contains button edit menu)
        """
        self.bottomframe.grid_remove()

    def showEditMenu(self):
        """
        shows bottom frame (contains button edit menu)
        """
        self.bottomframe.grid()

    def showButtons(self):
        """
        shows button frame & left sidebar
        removes multi-action frame
        """
        self.MAframe.grid_remove()
        self.lframe.grid()
        self.topframe.grid()
        self.button_hkey.grid()
        # self.button_clr.grid()

        self.current_button = None
        # get button index of parent button so we can call button_callback
        button_ix = None
        for i in range(len(self.buttons)):
            if self.parent_button is self.buttons[i]:
                button_ix = i
                break

        self.button_callback(button_ix)

        self.parent_button = None
        self.MAframe_active = False

    def showActionMenu(self):
        """
        hides button frame & left sidebar
        adds multi-action frame
        """
        self.topframe.grid_remove()
        self.lframe.grid_remove()
        self.button_hkey.grid_remove()
        # self.button_clr.grid_remove()
        self.MAframe.grid()
        self.hideEditMenu()

        self.parent_button = self.current_button
        self.current_button = None
        self.MAframe_active = True

    def hideSidebar(self):
        self.lframe.grid_remove()

    def showSidebar(self):
        self.lframe.grid()

    def changeViewMode(self):
        if self.viewmode == 0:
            self.viewmode = 1
            self.hideEditMenu()
            self.hideSidebar()

            # change dimensions of window
            self.geometry(
                f"{self.topframe.winfo_width()}x{self.topframe.winfo_height()}"
            )

            # pin window
            self.attributes("-topmost", True)
        else:
            self.viewmode = 0
            self.geometry(f"{XDIM}x{YDIM}")
            # self.showEditMenu()
            self.showSidebar()

            # unpin window
            self.attributes("-topmost", False)

            # reset current button because editor isn't shown
            if self.current_button is None:
                return
            self.current_button.configure(border_color=BC_DEFAULT)
            self.current_button = None

    def selectfile(self, filetypes):
        """
        Opens file explorer window to select a file whose type is in filetypes.
        If a file is chosen, current button's arg is set to the file path and button's text is the filename
        """

        if self.current_button is None:
            self.helpertxt_nobtn()
            return

        self.helpertxt_clear()  # in case there is a "NO FILE SELECTED" message

        f = tk.filedialog.askopenfilename(
            title="Choose song", initialdir=self.initialdir, filetypes=filetypes
        )

        if not f:
            return

        self.initialdir = os.path.dirname(f)  # remember dir we used

        # configure button text
        self.current_button.set_text(os.path.basename(f).split(".")[0], default=True)
        self.text_shared.set(
            self.current_button.cget("text")
        )  # re-fill entry text in case it changed

        # set button action and arg
        self.current_button.set_arg(f)

    def set_actionbutton(self, action_text, changed):
        """
        displays action-specific widget in the "edit button" menu
        "flex button" = class attribute that points to this widget
        """
        self.text_shared.set(self.current_button.cget("text"))

        NAME_TO_ACTION[action_text].display_widget(self, changed)

    def set_action(self, action_text):
        """
        sets button action index
        sets default action text (if applicable)
        sets default action argument (if applicable)
        """
        if self.current_button is None:
            self.action.set(ACTIONS[0].name)
            self.helpertxt_nobtn()
            return

        action = NAME_TO_ACTION[action_text]

        if self.MAframe_active and isinstance(action, MultiAction):
            self.action.set(ACTIONS[0].name)
            self.helper.configure(text="Nested Multi Actions Unavailable")
            return

        # check if this is a real action
        if action.inactive():
            self.current_button.deactivate()  # sets arg ix to 0 & changes appearance
        else:
            self.current_button.activate()

            action.set_action(self.current_button)

        self.set_actionbutton(action_text, True)
        self.current_button.set_image()

    def get_actions(self):
        return ACTIONS

    def init_global_checkbox(self):
        """
        Global checkbox that toggles global state of a button in the main view
        """

        if self.global_checkbox is not None:
            return
        self.global_checkbox = ctk.CTkCheckBox(
            master=self.bottomframe,
            text="Global",
            onvalue=True,
            offvalue=False,
            command=self.global_button,
        )
        self.global_checkbox.grid(row=0, column=0, padx=XPAD, pady=YPAD, sticky="nsew")

    def destroy_flex(self):
        """
        destroys the flex button if it exists
        """

        if self.flex_button is not None:
            try:
                self.flex_button.destroy()
            except ValueError:
                # some weird error with fonts
                pass
            self.flex_button = None

        if self.flex_button2 is not None:
            try:
                self.flex_button2.destroy()
            except ValueError:
                # some weird error with fonts
                pass
            self.flex_button2 = None

    def destroy_global_checkbox(self):
        """
        destroys the global checkbox if it exists
        """

        if self.global_checkbox is not None:
            self.global_checkbox.destroy()
            self.global_checkbox = None

    def global_button(self):
        """
        sets current button to be global if the checkbox is true
        """

        if self.current_button is None:
            self.helpertxt_nobtn()
            return

        if self.global_checkbox.get():
            self.current_button._global = True
        else:
            self.current_button._global = False

    def new_view(self, ix=None, duplicate=False):
        """
        Creates new view.
        If duplicate=False, then creates an empty view at ix (or at the end if ix is None)
        If duplicate=True, the view at ix is duplicated and placed below it
        """

        # reset active button
        if self.current_button is not None:
            self.current_button.configure(border_color=BC_DEFAULT)
            self.current_button = None

        self.destroy_flex()
        self.hideEditMenu()
        self.views[self.current_view].update(self.buttons)

        if ix is None:
            ix = len(self.views)

        # create unique name
        if duplicate:
            newname = str(self.views[ix])
        else:
            newname = f"View {len(self.views)+1}"
        usednames = [str(v) for v in self.views]
        if newname in usednames:
            i = 1
            while True:
                if f"{newname} ({i})" not in usednames:
                    newname = f"{newname} ({i})"
                    break
                i += 1

        # create new View instance
        if duplicate:
            newview = View(newname, self.views[ix].configs, False)
            ix += 1  # goes below original
        else:
            newview = View(newname, self.empty_view.configs, False)

        # insert view
        self.views.insert(ix, newview)

        if ix < len(self.views) - 1:
            # adjust args for buttons whose action is "Open View"
            changed = []
            for i, view in enumerate(self.views):
                if view.shift_views(ix):
                    changed.append(i)

            # refresh current view if affected
            if self.current_view in changed:
                self.views[self.current_view].to_buttons(
                    self.buttons, self.images, ACTION_ICONS
                )

            self.views[self.current_view].refresh_globals(
                self.buttons, self.views[0].configs
            )

        self.refresh_sidebar()

    def insert_view(self):
        """
        inserts empty view below the one that was right-clicked
        """
        self.new_view(self.view_edit_ix + 1, False)

    def duplicate_view(self):
        """
        duplicates a view and inserts it below the original
        """
        self.new_view(self.view_edit_ix, True)

    def move_view(self, up=True):
        """
        Moves a view's location in the left sidebar up or down by one spot
        """
        if up:
            if self.view_edit_ix <= 1:
                return  # keep main view at the top
            offset = -1
        else:
            if self.view_edit_ix == len(self.views) - 1 or self.view_edit_ix == 0:
                return
            offset = 1

        genericSwap(self.views, self.view_edit_ix, self.view_edit_ix + offset)

        # adjust args for any button whose action is "Open View"
        changed = []
        for i, view in enumerate(self.views):
            if view.swap_views(self.view_edit_ix, self.view_edit_ix + offset):
                changed.append(i)

        if (
            (self.view_edit_ix == self.current_view)
            or (self.view_edit_ix == self.current_view - 1 and not up)
            or (self.view_edit_ix == self.current_view + 1 and up)
        ):
            # switch views if current view moved
            self.views[self.current_view].to_buttons(
                self.buttons, self.images, ACTION_ICONS
            )
            self.buttons[
                self.back_button
            ].back_button()  # always run this because main view cannot move
        elif self.current_view in changed:
            # update view if args in this one changed
            self.views[self.current_view].to_buttons(
                self.buttons, self.images, ACTION_ICONS
            )

        self.views[self.current_view].refresh_globals(
            self.buttons, self.views[0].configs
        )

        self.refresh_sidebar()

    def delete_view(self):
        """
        Delete the view that was right clicked
        """

        to_delete = self.view_edit_ix
        if self.views[to_delete].ismain():
            self.helper.configure(text="CANNOT DELETE MAIN VIEW")
            return

        if to_delete == self.current_view:
            self.switch_view(view_enum=to_delete - 1)
        self.views.pop(to_delete)

        if to_delete < len(self.views):
            # adjust args for buttons whose action is "Open View"
            changed = []
            for i, view in enumerate(self.views):
                if view.shift_views(to_delete, up=False):
                    changed.append(i)

            # refresh current view if affected
            if self.current_view in changed:
                self.views[self.current_view].to_buttons(
                    self.buttons, self.images, ACTION_ICONS
                )

            self.views[self.current_view].refresh_globals(
                self.buttons, self.views[0].configs
            )

        self.refresh_sidebar()

    def rename_view1(self):
        """
        Allows user to edit view name
        """

        # get current name
        curname = str(self.views[self.view_edit_ix])

        # create text variable
        view_name = tk.StringVar(self.bottomframe, value="")

        # change right-clicked button to entry widget
        self.viewbuttons[self.view_edit_ix].destroy()
        rename_entry = ctk.CTkEntry(
            self.lframe,
            corner_radius=0,
            height=40,
            placeholder_text=curname,
            font=self.STANDARDFONT,
            textvariable=view_name,
        )
        rename_entry.grid(
            row=self.view_edit_ix + 1, column=0, sticky="ew"
        )  # +1 for new view button
        rename_entry.insert(0, curname)
        rename_entry.icursor(len(curname))
        rename_entry.focus()

        # bind unfocus and Enter (key) to finish the rename process
        rename_entry.bind("<FocusOut>", self.rename_view2)
        rename_entry.bind("<Return>", self.rename_view2)

        # add entry widget to viewbuttons
        self.viewbuttons[self.view_edit_ix] = rename_entry

    def rename_view2(self, event):
        """
        Changes name of view after editing is complete
        """

        name = self.viewbuttons[self.view_edit_ix].get()
        if name in [str(v) for v in self.views]:
            self.helper.configure(text="Name already in use")
        else:
            self.views[self.view_edit_ix].rename(name)

        self.refresh_sidebar()  # changes name and reverts entry widget to buttons

    def name_to_ix(self, view_name):
        """
        Converts view name to index in self.views
        """

        view_enum = -1
        for i in range(len(self.views)):
            if str(self.views[i]) == view_name:
                view_enum = i
                break

        if view_enum == -1:
            raise ValueError(view_name)

        return view_enum

    def switch_view(self, view_enum=None, save=True):
        """
        Switches to new view
        Must be called by mainloop
        """

        if view_enum is None:
            if self.view_enum is not None:
                view_enum = self.view_enum
            else:
                raise TypeError

        # reset active buttons
        if self.current_button is not None:
            self.current_button.configure(border_color=BC_DEFAULT)
            self.current_button = None
        self.destroy_flex()

        if view_enum == self.current_view:
            return

        # save current view:
        if save:
            self.views[self.current_view].update(self.buttons)

        # on the sidebar, highlight new view button and unhighlight old one:
        self.viewbuttons[view_enum].configure(fg_color=("gray70", "gray30"))
        self.viewbuttons[self.current_view].configure(fg_color="transparent")

        # open new view:
        if self.views[view_enum].ismain():
            self.buttons[self.back_button].unlock()
        else:
            self.destroy_global_checkbox()
        self.views[view_enum].to_buttons(self.buttons, self.images, ACTION_ICONS)

        # handle back button & locking
        if not self.views[view_enum].ismain():
            self.buttons[self.back_button].back_button()

        self.current_view = view_enum

    def save_data(self):
        """
        Write views, images, and globals to disk
        """

        # save current view:
        self.reset_bordercols()
        self.views[self.current_view].update(self.buttons)

        # gather layout data
        data_views = {}
        for view in self.views:
            # convert from action enum to uid
            configs = view.configs
            for config in configs:
                if config[0] == len(ACTIONS) - 1:
                    for config2 in config[1]:
                        config2[0] = ENUM_TO_UID[config2[0]]
                config[0] = ENUM_TO_UID[config[0]]
            data_views[str(view)] = configs

        try:
            # load save file:
            with open("savedata.json", "r") as f:
                savedata = json.load(f)
        except FileNotFoundError:
            # create blank save file
            savedata = {}
            savedata["layouts"] = {}

        # overwrite views for layout we're using:
        savedata["layouts"][self.key_layout] = data_views

        # overwrite image array
        savedata["images"] = [img._light_image.filename for img in self.images]

        # overwrite globals array
        if "globals" not in savedata.keys():
            savedata["globals"] = {}
        savedata["globals"][self.key_layout] = [
            button._global for button in self.buttons
        ]

        with open("savedata.json", "w") as f:
            json.dump(savedata, f)

        print("saved data to savedata.json")

    def load_imgs(self, savedata):
        """
        loads images from disk
        """

        data = savedata["images"]

        self.images = [ctkimage(elem, ICON_SIZE) for elem in data]

    def load_views(self, savedata):
        """
        loads views from disk
        """

        data = savedata["layouts"][self.key_layout]

        self.views = []
        for name, configs in data.items():
            # convert from Action uid to Enum
            for config in configs:
                config[0] = UID_TO_ENUM[config[0]]
                if config[0] == len(ACTIONS) - 1:  # is multi action
                    for config2 in config[1]:
                        config2[0] = UID_TO_ENUM[config2[0]]
            self.views.append(View(name, configs, False))

        self.views[0].to_buttons(self.buttons, self.images, ACTION_ICONS, set_keys=True)

        # store colors
        for view in self.views:
            self.used_colors |= view.colors()

    def load_globals(self, savedata):
        """
        load global button status into main view
        """

        global_buttons = savedata["globals"][self.key_layout]
        for i in range(len(self.buttons)):
            self.buttons[i]._global = global_buttons[i]

    def refresh_sidebar(self, init=False):
        """
        updates view data and current selection in left sidebar
        """

        if not init:
            for button in self.viewbuttons:
                button.destroy()
        self.viewbuttons = []
        for i, view in enumerate(self.views):
            fg_color = ("gray70", "gray30") if i == self.current_view else "transparent"
            newbutton = ViewButton(
                self.lframe,
                corner_radius=4,
                height=40,
                border_spacing=10,
                text=str(view),
                fg_color=fg_color,
                font=self.STANDARDFONT,
                hover_color=("gray70", "gray30"),
                anchor="w",
                command=partial(self.switch_view, view_enum=i),
            )
            newbutton.grid(row=i + 1, column=0, sticky="ew")  # +1 for new view button

            # add right click callback and bind right click to it
            newbutton.set_callback(self, i)
            newbutton.bind("<Button-3>", newbutton.rclick)

            self.viewbuttons.append(newbutton)

    def arg_from_text(self, *args):
        """
        Sets current button arg to whatever is in App.flex_text
        """

        self.current_button.set_arg(self.flex_text.get())

    def view_from_dropdown(self, view_name):
        """
        sets arg and defaulttext of current button for "Open View" action
        """

        self.current_button.set_arg(self.name_to_ix(view_name))
        self.current_button.set_text(view_name, default=True)

    def arg_from_dropdown(self, arg):
        """
        sets arg and defaulttext of current button to the dropdown selection
        """

        self.current_button.set_arg(arg)
        self.current_button.set_text(arg, default=True)

    def choosecolor(self):
        """
        Opens AskColor window,
        updates button color and self.used_colors if a color is returned
        """

        if self.current_button is not None:
            # get current color to initialize window
            current_color = self.current_button.cget("fg_color")
            if len(current_color) == 2:
                current_color = current_color[1]  # dark theme color is second
            current_color = to_rgb(current_color)
            pick_color = AskColor(self.used_colors, color=current_color)
            color = pick_color.get()
            if color is None:
                # exited without choosing a color
                return
            self.used_colors.add(color)
            self.current_button.set_colors(
                fg_color=color, border_color=None, hover_color=hovercolor(color)
            )
        else:
            self.helpertxt_nobtn()

    def renamebutton(self, *args):
        """
        renames current button to App.text_shared's value
        """

        # args has metadata on the variable who called us
        if self.current_button is not None:
            if not self.MAframe_active:
                self.current_button.set_text(self.text_shared.get())
            else:
                self.current_button.set_text(self.text_shared.get(), wraplen=WRAPLEN_MA)
        else:
            self.helpertxt_nobtn()

    def hkconfig(self):
        """
        Opens HotkeyWindow instance and changes a button's hotkey once closed
        """

        self.helpertxt_clear()
        if self.current_button is not None:
            win = HotkeyWindow(
                self.current_button.key, self.current_button.modifier, self.STANDARDFONT
            )
            newkeys = win.get()
            if newkeys is None:
                return

            # check if this hotkey is already mapped to a different key
            oldkeys = (
                self.current_button.get_keys()
            )  # store old keys in case we need to revert
            curhotkeys = Keyboard.hotkeymap(self.buttons)

            self.current_button.set_keys(newkeys[0], newkeys[1])
            newhotkeys = Keyboard.hotkeymap(self.buttons)

            if len(curhotkeys) > len(newhotkeys):
                self.helper.configure(text="KEY COMBINATION ALREADY IN USE")
                self.current_button.set_keys(oldkeys[0], oldkeys[1])
                return

            self.kill_hotkeys()
            self.init_hotkeys()
        else:
            self.helpertxt_nobtn()

    def imgconfig(self):
        """
        opens ImageWindow instance and changes a button's image once closed
        """

        self.helpertxt_clear()
        if self.current_button is not None:
            win = ImageWindow(self.images, self.STANDARDFONT)
            newimg = win.get()
            if newimg is None:
                return

            # check if this image is new
            for ix, img in enumerate(self.images):
                fname = img._light_image.filename
                if os.path.basename(newimg._light_image.filename) == os.path.basename(
                    fname
                ):
                    # set image, don't add to self.images
                    self.current_button.set_image(ix, self.images)
                    return

            self.images.append(newimg)

            # change button image
            self.current_button.set_image(len(self.images) - 1, self.images)

        else:
            self.helpertxt_nobtn()

    def reset_bordercols(self):
        """
        sets all actionbutton borders to default color

        could be optimized # TODO
        """

        for button in self.buttons:
            button.configure(border_color=BC_DEFAULT)

    def entryconfig(self, event):
        """
        Unfocuses current button when we click on something else.
        Bound to left click
        """

        if isinstance(event.widget, ctk.windows.ctk_tk.CTk):
            if self.current_button is not None:
                self.current_button.configure(border_color=BC_DEFAULT)
                self.current_button = None
            # self.destroy_flex()
            self.hideEditMenu()
        try:
            event.widget.focus_set()
        except AttributeError:  # from color picker
            pass

    def rclick_popup(self, event, view_ix):
        """
        does popup menu if view was right clicked in the sidebar
        """

        self.view_edit_ix = view_ix
        self.rclickmenu.tk_popup(event.x_root, event.y_root)
        self.rclickmenu.grab_release()

    def helpertxt_clear(self):
        self.helper.configure(text="")

    def helpertxt_noconfig(self):
        self.helper.configure(text="BUTTON NOT CONFIGURED")

    def helpertxt_nobtn(self):
        self.helper.configure(text="NO BUTTON SELECTED")

    def _on_closing(self):
        self.save_data()
        if self.obsws is not None:
            self.obsws.disconnect()
        self.destroy()

    ####################################
    # LAYOUT SETUP
    ####################################

    def numpad_buttongrid(self, key_layout):
        """
        Loads key layout from file and creates button grid according to specifications

        Runs once during init
        """

        with open(key_layout, "r") as f:
            button_mapping = json.load(f)

        buttons = []
        frame = self.topframe

        self.back_button = -1

        for i, key in enumerate(button_mapping.keys()):
            xadjustment = BUTTON_SIZES[button_mapping[key]["attr"]][1]
            yadjustment = BUTTON_SIZES[button_mapping[key]["attr"]][0]
            button = ActionButton(
                frame,
                #    command=mapping[key]['callback'],
                command=partial(self.button_callback, i),
                text="asdf",  # dummy text due to bug
                width=85 * xadjustment + 2 * XPAD * (xadjustment - 1),
                height=85 * yadjustment + 2 * YPAD * (yadjustment - 1),
                border_width=2,
                fg_color=FC_EMPTY,
                hover_color=HC_EMPTY,
                border_color=BC_DEFAULT,
                font=self.STANDARDFONT,
                anchor="n",
                compound="bottom",
            )

            button.set_keys(
                ""
                if button_mapping[key]["modifier"] is None
                else button_mapping[key]["modifier"],
                key,
            )
            button._text_label.configure(wraplength=WRAPLEN * xadjustment)

            # undo dummy values
            button.configure(text="")

            button.grid(
                row=button_mapping[key]["y"],
                column=button_mapping[key]["x"],
                padx=XPAD,
                pady=YPAD,
                rowspan=yadjustment,
                columnspan=xadjustment,
            )
            button.grid_propagate(0)  # prevents vertical stretching with text
            buttons.append(button)

            if button_mapping[key]["y"] == 0 and button_mapping[key]["x"] == 0:
                self.back_button = i

        if self.back_button < 0:
            raise ValueError(
                f"{key_layout} missing button in top left corner (required for back button)"
            )
        return buttons

    def button_settings(self):
        """
        Creates widgets for button settings

        Runs once during init
        """

        frame = self.bottomframe

        # helper text
        helper = ctk.CTkLabel(frame, text="", font=self.STANDARDFONT)
        helper.grid(row=0, column=1, columnspan=2, padx=XPAD, pady=YPAD, sticky="nsew")

        # Button Text
        txtbox = ctk.CTkEntry(
            frame,
            placeholder_text="Button Text",
            textvariable=self.text_shared,
            font=self.STANDARDFONT,
        )
        txtbox.grid(row=1, column=0, columnspan=3, padx=XPAD, pady=YPAD, sticky="nsew")

        # Button Action
        action = ctk.CTkOptionMenu(
            frame,
            values=[action.name for action in ACTIONS],
            command=self.set_action,
            fg_color=FC_DEFAULT2,
            button_color=FC_DEFAULT2,
            button_hover_color=hovercolor(FC_DEFAULT2),
            dynamic_resizing=False,
            font=self.STANDARDFONT,
        )
        action.grid(row=2, column=0, padx=XPAD, pady=YPAD, sticky="nsew")

        # Button Color
        button_clr = ctk.CTkButton(
            frame,
            command=self.choosecolor,
            text="Color",
            fg_color=BC_DEFAULT,
            hover_color=hovercolor(BC_DEFAULT),
            font=self.STANDARDFONT,
        )
        button_clr.grid(row=3, column=0, padx=XPAD, pady=YPAD, sticky="nsew")

        # Button Image:
        button_img = ctk.CTkButton(
            frame,
            command=self.imgconfig,
            text="Image",
            fg_color=BC_DEFAULT,
            hover_color=hovercolor(BC_DEFAULT),
            font=self.STANDARDFONT,
        )
        button_img.grid(
            row=3, column=1, columnspan=1, padx=XPAD, pady=YPAD, sticky="nsew"
        )

        # Button HotKey:
        button_hkey = ctk.CTkButton(
            frame,
            command=self.hkconfig,
            text="Hotkey",
            fg_color=BC_DEFAULT,
            hover_color=hovercolor(BC_DEFAULT),
            font=self.STANDARDFONT,
        )
        button_hkey.grid(row=3, column=2, padx=XPAD, pady=YPAD, sticky="nsew")

        return helper, txtbox, action, button_clr, button_hkey

    def createEmptyMenu(self):
        """
        creates and returns tkinter menu with custom formatting
        """

        return tk.Menu(
            self,
            tearoff=0,
            font=self.SMALLFONT,
            fg="white",
            background=FC_EMPTY,
            activebackground="gray30",
            bd=1,
            relief=None,
        )

    def createMenuBar(self):
        """
        creates tkinter menu bar for app
        """

        mainmenu = self.createEmptyMenu()

        # filemenu # TODO

        viewmenu = self.createEmptyMenu()
        mainmenu.add_cascade(label="View", menu=viewmenu)
        viewmenu.add_command(label="Toggle View", command=self.changeViewMode)

        return mainmenu

    def createViewMenu(self):
        """
        creates tkinter menu for view sidebar
        """

        m = self.createEmptyMenu()
        m.add_command(label="Rename", command=self.rename_view1)
        m.add_command(label="Insert", command=self.insert_view)
        m.add_command(label="Duplicate", command=self.duplicate_view)
        m.add_separator()
        m.add_command(label="Move Up", command=partial(self.move_view, True))
        m.add_command(label="Move Down", command=partial(self.move_view, False))
        m.add_separator()
        m.add_command(label="Delete", command=self.delete_view)

        return m
