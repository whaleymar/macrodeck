import tkinter as tk
import customtkinter as ctk
from macrodeck.gui.util import hovercolor, to_rgb, ctkimage
import os
import macrodeck.VLCPlayer as VLCPlayer
import macrodeck.Keyboard as Keyboard
import macrodeck.KeyCategories as KeyCategories
from macrodeck.gui.ActionButton import ActionButton
from macrodeck.gui.ButtonView import View, ViewButton
from macrodeck.gui.ColorPicker import AskColor # from https://github.com/Akascape/CTkColorPicker
from macrodeck.gui.HotkeyWindow import HotkeyWindow
from macrodeck.gui.ImageWindow import ImageWindow
from macrodeck.gui.MacroWindow import MacroWindow
from macrodeck.gui.style import BC_ACTIVE, BC_DEFAULT, FC_DEFAULT, FC_EMPTY, WRAPLEN, ICON_SIZE, ICON_SIZE_WIDE
from functools import partial
import json
import webbrowser as web

####################################
# WINDOW APPEARANCE
####################################
ctk.set_appearance_mode("System")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

####################################
# HELPERS
####################################

def do_nothing():
    pass

####################################
# CONSTANTS
####################################

# geo
XDIM = 800
YDIM = 800 # 700 good for normal numpad
XPAD = 5
YPAD = 5

BUTTON_SIZES = {
    'regular':(1,1),
    'tall':(2,1),
    'wide':(1,2)
}

DEFAULT_MODIFIER = KeyCategories.MODIFIERKEYSHOTKEY[3]

ACTION_VALUES = ['No Action', 'Play Media', 'Stop Media', 'Pause Media', 'Open View', 'Perform Macro', 'Open Web Page']
ACTION_ARGS = [None, None, None, None, 0, None, ""] # default action args
ACTION_ICONS = [None, ctkimage('assets/action_audio.png', ICON_SIZE_WIDE), ctkimage('assets/action_mute.png', ICON_SIZE),
                ctkimage('assets/action_pause.png', ICON_SIZE),ctkimage('assets/action_openview.png', ICON_SIZE),
                ctkimage('assets/action_macro.png', ICON_SIZE), ctkimage('assets/action_web.png', ICON_SIZE)]

HC_EMPTY = hovercolor(FC_EMPTY)
HC_DEFAULT = hovercolor(FC_DEFAULT)

class App(ctk.CTk):
    def __init__(self, key_layout):
        super().__init__()

        self.geometry(f"{XDIM}x{YDIM}")
        self.STANDARDFONT = ctk.CTkFont(family='Arial', weight='bold', size=14) # default size is 13
        self.SMALLFONT = ctk.CTkFont(family='Arial', size=14) # default size is 13

        # init VLC player
        self.player = VLCPlayer.VLCPlayer()

        # init macro keyboard
        self.keyboard = Keyboard.keyboard()

        # make all widgets focus-able so I can click out of entry box:
        # also make buttons un-focusable by clicking outside of a widget
        self.bind_all("<1>", lambda event: self.entryconfig(event))

        # init right click menu for views:
        self.rclickmenu = self.createViewMenu()

        # save views on closing:
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        ####################################
        # FRAMES
        ####################################

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # BOTTOM (button settings)
        self.bottomframe = ctk.CTkFrame(self, width = (XDIM/2 - XPAD*2), height = (YDIM - YPAD*2))
        self.bottomframe.grid(row=1, column=1, sticky='')

        # LEFT SIDEBAR (view selection)
        self.lframe = ctk.CTkScrollableFrame(self, corner_radius=0, height=YDIM)
        self.lframe.grid(row=0, column=0, rowspan=2, sticky='nsew')
        self.lframe.grid_columnconfigure(0,weight=1)
        self.newviewbutton = ctk.CTkButton(self.lframe, corner_radius=0, height=40, border_spacing=10,
                                                text="New View", 
                                                font=self.STANDARDFONT,
                                                anchor='w', command=self.new_view)
        self.newviewbutton.grid(row=0, column=0, sticky='ew')

        # TOP (button grid)
        self.topframe = ctk.CTkFrame(self, width = (XDIM/2 - XPAD*2), height = (YDIM - YPAD*2))
        self.topframe.grid(row=0, column=1, sticky='')


        ####################################
        # MISC
        ####################################

        self.text_shared = tk.StringVar(self.bottomframe, value='')
        self.text_shared.trace('w',self.renamebutton) # callback when text is edited

        self.current_button = None

        self.initialdir = '/' # where we start when opening a file
        self.flex_button = None
        self.flex_text = None
        self.global_checkbox = None
        self.to_press = None

        self.key_layout = os.path.basename(key_layout)[:-5] # name of layout file without extension
        self.buttons = self.numpad_buttongrid(key_layout)
        self.helper, self.txtbox, self.action, self.button_clr = self.button_settings()

        # load save:
        try:
            with open('savedata.json', 'r') as f:
                savedata = json.load(f)
        except FileNotFoundError:
            savedata = None

        ####################################
        # IMAGES
        ####################################
        if savedata is None:
            self.images = [icon for icon in ACTION_ICONS if icon is not None]
        else:
            try:
                self.load_imgs(savedata)
            except KeyError:
                self.images = [icon for icon in ACTION_ICONS if icon is not None]

        ####################################
        # VIEWS
        ####################################

        # store empty view -- blank slate for new views
        self.empty_view = View('View 1', self.buttons)

        # load views
        self.used_colors = {FC_DEFAULT, FC_EMPTY}
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
    
    # return callbacks to be used as globals
    def _callbacks(self):
        return [do_nothing, self.player.__call__, self.player.reset, self.player.toggle_pause, self.open_view, self.schedule_macro, web.open]
    
    def init_hotkeys(self):
        self.hotkeys = Keyboard.init_hotkeys(self.buttons) # inherits from threading.thread
        self.hotkeys.start()

    def kill_hotkeys(self):
        self.hotkeys.stop()
        self.hotkeys = None
    
    def button_callback(self, button_ix):
        # run button action if it was already selected
        if self.current_button is self.buttons[button_ix]:
            self.current_button.run_action()
            return
        
        # reset dynamic vars
        self.reset_bordercols()
        self.helpertxt_clear()
        self.current_button = self.buttons[button_ix]

        # set current button options in GUI:
        self.text_shared.set(self.current_button.cget("text"))
        self.current_button.configure(border_color=BC_ACTIVE)
        b_action = ACTION_VALUES[self.current_button.action_enum]
        self.action.set(b_action)
        self.set_actionbutton(b_action, False)

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

    def selectfile(self):
        self.helpertxt_clear() # in case there is a "NO FILE SELECTED" message
        if self.current_button is not None:
            filetypes = (
                ('MP3 files', '*.mp3'),
                ('All Files', '*.*')
            )

            f = tk.filedialog.askopenfilename(
                title='Choose song',
                initialdir=self.initialdir,
                filetypes=filetypes
            )
            
            if f:
                self.initialdir = os.path.dirname(f) # remember dir we used

                # configure button text
                self.current_button.set_text(os.path.basename(f).split('.')[0], default=True)
                self.text_shared.set(self.current_button.cget("text")) # re-fill entry text in case it changed

                # set button action and arg
                self.current_button.set_arg(f)
        else:
            self.helpertxt_nobtn()

    # displays correct widget based on button action
    def set_actionbutton(self, action_text, changed):
        self.text_shared.set(self.current_button.cget("text"))

        if action_text == 'No Action':
            self.destroy_flex()
        
        elif action_text == 'Play Media':
            self.init_media_button()

        elif action_text == 'Stop Media':
            self.destroy_flex()

        elif action_text == 'Pause Media':
            self.destroy_flex()

        elif action_text == 'Open View':
            self.init_view_button()

        elif action_text == 'Perform Macro':
            self.init_macro_button()

        elif action_text == 'Open Web Page':
            self.init_URL_entry()
            if not changed:
                self.flex_text.set(self.current_button.arg)

        else:
            raise ValueError(action_text)

    # sets button action index
    # sets default action text (if applicable)
    # sets default action argument (if applicable)
    def set_action(self, action_text):
        if self.current_button is None:
            self.action.set(ACTION_VALUES[0])
            self.helpertxt_nobtn()
            return
            
        # check if we are mapping a real action
        if action_text == 'No Action':
            self.current_button.deactivate() # sets arg ix to 0 & changes appearance
        else:
            self.current_button.activate()

            if action_text == 'Play Media':
                self.current_button.set_action(1)

            elif action_text == 'Stop Media':
                self.current_button.set_action(2)
                self.current_button.set_text('Stop Audio', default=True)

            elif action_text == 'Pause Media':
                self.current_button.set_action(3)
                self.current_button.set_text('Pause Audio', default=True)

            elif action_text == 'Open View':
                self.current_button.set_action(4)
                self.current_button.set_text(str(self.views[0]), default=True)

            elif action_text == 'Perform Macro':
                self.current_button.set_action(5)
                pass # not implemented

            elif action_text == 'Open Web Page':
                self.current_button.set_action(6)

            else:
                raise ValueError(action_text)

        self.current_button.set_arg(ACTION_ARGS[self.current_button.get_action()])
        self.set_actionbutton(action_text, True)
        self.current_button.set_image()

    # sets flex button to media chooser button
    def init_media_button(self):
        # display media button on bottomframe

        self.destroy_flex()

        button_clr = ctk.CTkButton(self.bottomframe, 
                                command=self.selectfile, 
                                text='Choose File',
                                font=self.STANDARDFONT)
        button_clr.grid(row=2, column=1, padx=XPAD, pady=YPAD, sticky='w')

        self.flex_button = button_clr

    # sets flex button to view optionmenu
    def init_view_button(self):
        self.destroy_flex()
        views = [str(l) for l in self.views]

        button_view = ctk.CTkOptionMenu(self.bottomframe,
                                command=self.arg_from_dropdown, 
                                values=views,
                                font=self.STANDARDFONT)
        
        button_view.set(str(self.views[self.current_button.arg]))

        # set button default text
        if self.current_button is not self.buttons[self.back_button] or self.views[self.current_view].ismain():
            self.arg_from_dropdown(button_view.get())

        button_view.grid(row=2, column=1, padx=XPAD, pady=YPAD, sticky='w')

        self.flex_button = button_view

    def init_URL_entry(self):
        self.destroy_flex()

        self.flex_text = tk.StringVar(self.bottomframe, value='')
        self.flex_text.trace('w',self.arg_from_text) # sets URL argument

        entry = ctk.CTkEntry(self.bottomframe, textvariable=self.flex_text)
        entry.grid(row=2, column=1, padx=XPAD, pady=YPAD, sticky='w')
        self.flex_button = entry

    # set flex button to macro
    def init_macro_button(self):
        self.destroy_flex()

        button = ctk.CTkButton(self.bottomframe, 
                                command=self.macroconfig, 
                                text='Set Macro',
                                font=self.STANDARDFONT)
        button.grid(row=2, column=1, padx=XPAD, pady=YPAD, sticky='w')

        self.flex_button = button

    def init_global_checkbox(self):
        if self.global_checkbox is not None:
            return
        self.global_checkbox = ctk.CTkCheckBox(master=self.bottomframe, text="Global", 
                                               onvalue=True, offvalue=False, 
                                               command = self.global_button)
        self.global_checkbox.grid(row=4, column=0, padx=XPAD, pady=YPAD, sticky='nsw')

    def destroy_flex(self):
        if self.flex_button is not None:
            self.flex_button.destroy()
            self.flex_button = None

    def destroy_global_checkbox(self):
        if self.global_checkbox is not None:
            self.global_checkbox.destroy()
            self.global_checkbox = None

    def global_button(self):
        if self.current_button is None:
            self.helpertxt_nobtn()
            return
        
        if self.global_checkbox.get():
            self.current_button._global = True
        else:
            self.current_button._global = False

    def new_view(self):
        # reset active button
        if self.current_button is not None:
                self.current_button.configure(border_color=BC_DEFAULT)
                self.current_button = None

        self.destroy_flex()
        # self.views.append(View(f'View {len(self.views)+1}', self.buttons)) # copy current view
        
        # append empty view
        self.views.append(View(f'View {len(self.views)+1}', self.empty_view.configs, False))
        self.refresh_sidebar()

    # delete view that was right clicked
    def delete_view(self):
        to_delete = self.view_edit_ix
        if self.views[to_delete].ismain():
            self.helper.configure(text='CANNOT DELETE MAIN VIEW')
        else:
            if to_delete == self.current_view:
                self.switch_view(to_delete-1)
            self.views.pop(to_delete)
            self.refresh_sidebar()

    # init rename process
    def rename_view1(self):
        # get current name
        curname = str(self.views[self.view_edit_ix])

        # create text variable
        view_name = tk.StringVar(self.bottomframe, value='')

        # change right-clicked button to entry widget
        self.viewbuttons[self.view_edit_ix].destroy()
        rename_entry = ctk.CTkEntry(self.lframe, corner_radius=0, height=40, 
                                      placeholder_text=curname, 
                                      font=self.STANDARDFONT, 
                                      textvariable=view_name
                                      )
        rename_entry.grid(row=self.view_edit_ix+1, column=0, sticky='ew') # +1 for new view button
        rename_entry.insert(0, curname)
        rename_entry.icursor(len(curname))
        rename_entry.focus()

        # bind unfocus and Enter (key) to finish the rename process
        rename_entry.bind('<FocusOut>', self.rename_view2)
        rename_entry.bind('<Return>', self.rename_view2)

        # add entry widget to viewbuttons
        self.viewbuttons[self.view_edit_ix] = rename_entry

    # complete rename process
    def rename_view2(self, event): 
        name = self.viewbuttons[self.view_edit_ix].get()
        self.views[self.view_edit_ix].rename(name)
        self.refresh_sidebar() # changes name and reverts entry widget to buttons

    def name_to_enum(self, view_name):
        view_enum = -1
        for i in range(len(self.views)):
            if str(self.views[i]) == view_name:
                view_enum = i
                break

        if view_enum == -1:
            raise ValueError(view_name)
        
        return view_enum

    # keyboard listener must use this callback 
    def open_view(self, view_enum):
        self.view_enum = view_enum
        self.after(0, self.switch_view)

    # this is only called by mainloop
    def switch_view(self, view_enum=None):

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
        
        if view_enum == self.current_view: return

        # save current view:
        self.views[self.current_view].update(self.buttons)

        # on the sidebar, highlight new view button and unhighlight old one:
        self.viewbuttons[view_enum].configure(fg_color=('gray70', 'gray30'))
        self.viewbuttons[self.current_view].configure(fg_color='transparent')

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

    # write view and image info to disk
    def save_data(self):
        # save current view:
        self.reset_bordercols()
        self.views[self.current_view].update(self.buttons)

        # gather layout data
        data_views = {}
        for view in self.views:
            data_views[str(view)] = view.configs

        # load save file:
        with open('savedata.json', 'r') as f:
            savedata = json.load(f)

        # overwrite views for layout we're using:
        savedata['layouts'][self.key_layout] = data_views

        # overwrite image array
        savedata['images'] = [img._light_image.filename for img in self.images]

        # overwrite globals array
        if 'globals' not in savedata.keys():
            savedata['globals']={}
        savedata['globals'][self.key_layout] = [button._global for button in self.buttons]

        with open('savedata.json', 'w') as f:
            json.dump(savedata, f)
        
        print("saved data to savedata.json")

    def load_imgs(self, savedata):

        data = savedata['images']

        self.images = [ctkimage(elem, ICON_SIZE) for elem in data]

    def load_views(self, savedata):

        data = savedata['layouts'][self.key_layout]
        
        self.views = []
        for k,v in data.items():
            self.views.append(View(k, v, False))
        
        self.views[0].to_buttons(self.buttons, self.images, ACTION_ICONS, set_keys=True)

        # store colors
        for view in self.views:
            self.used_colors |= view.colors()

    # load global button status into main view
    def load_globals(self, savedata):
        global_buttons = savedata['globals'][self.key_layout]
        for i in range(len(self.buttons)):
            self.buttons[i]._global = global_buttons[i]

    def refresh_sidebar(self, init=False):
        if not init:
            for button in self.viewbuttons:
                button.destroy()
        self.viewbuttons = []
        for i,view in enumerate(self.views):
            fg_color = ('gray70', 'gray30') if i==self.current_view else 'transparent'
            newbutton = ViewButton(self.lframe, corner_radius=0, height=40, border_spacing=10,
                                      text=str(view), fg_color=fg_color, 
                                      font=self.STANDARDFONT, hover_color=('gray70', 'gray30'),
                                      anchor='w', 
                                      command=partial(self.switch_view,i)
                                      )
            newbutton.grid(row=i+1, column=0, sticky='ew') # +1 for new view button

            # add right click callback and bind right click to it
            newbutton.set_callback(self, i)
            newbutton.bind("<Button-3>", newbutton.rclick)

            self.viewbuttons.append(newbutton)

    def arg_from_text(self, *args):
        self.current_button.set_arg(self.flex_text.get())

    # sets arg and defaulttext of current button for "Open View" action
    def arg_from_dropdown(self, view_name):
        self.current_button.set_arg(self.name_to_enum(view_name))
        self.current_button.set_text(view_name, default=True)

    def choosecolor(self):
        if self.current_button is not None:
            # get current color to initialize window
            current_color = self.current_button.cget('fg_color')
            if len(current_color)==2: current_color=current_color[1] # dark theme color is second
            current_color = to_rgb(current_color)
            pick_color = AskColor(self.used_colors, color = current_color)
            color = pick_color.get()
            if color is None:
                # exited without choosing a color
                return
            self.used_colors.add(color)
            self.current_button.set_colors(fg_color=color, border_color=None, hover_color=hovercolor(color))
        else:
            self.helpertxt_nobtn()

    def renamebutton(self, *args): 
        # args has metadata on the variable who called us    
        if self.current_button is not None:
            self.current_button.set_text(self.text_shared.get())
        else:
            self.helpertxt_nobtn()

    def hkconfig(self):
        self.helpertxt_clear()
        if self.current_button is not None:
            win = HotkeyWindow(self.current_button.key, self.current_button.modifier, self.STANDARDFONT)
            newkeys = win.get()
            if newkeys is None:
                return
            
            # check if this hotkey is already mapped to a different key
            oldkeys = self.current_button.get_keys() # store old keys in case we need to revert
            curhotkeys = Keyboard.hotkeymap(self.buttons)

            self.current_button.set_keys(newkeys[0], newkeys[1])
            newhotkeys = Keyboard.hotkeymap(self.buttons)

            if len(curhotkeys) > len(newhotkeys):
                self.helper.configure(text='KEY COMBINATION ALREADY IN USE')
                self.current_button.set_keys(oldkeys[0], oldkeys[1])
                return
            
            self.hotkeys = Keyboard.reset_hotkeys(self.buttons, self.hotkeys)
        else:
            self.helpertxt_nobtn()

    def imgconfig(self):
        self.helpertxt_clear()
        if self.current_button is not None:
            win = ImageWindow(self.images, self.STANDARDFONT)
            newimg = win.get()
            if newimg is None:
                return
            
            # check if this image is new 
            for ix,img in enumerate(self.images):
                fname = img._light_image.filename
                if os.path.basename(newimg._light_image.filename) == os.path.basename(fname):
                    # set image, don't add to self.images 
                    self.current_button.set_image(ix, self.images)
                    return
            
            self.images.append(newimg)

            # change button image
            self.current_button.set_image(len(self.images)-1, self.images)

        else:
            self.helpertxt_nobtn()
    
    def macroconfig(self):
        self.helpertxt_clear()
        if self.current_button is None:
            self.helpertxt_nobtn()
            return

        win = MacroWindow(self.current_button.arg, self.STANDARDFONT)
        newmacro = win.get()
        if newmacro is None:
            return
        
        # convert modifiers with map
        for i in range(len(newmacro)):
            if newmacro[i][0]=='':continue
            newmacro[i] = ("+".join([KeyCategories.MODIFIER_TO_VK[key] for key in newmacro[i][0].split('+')]), newmacro[i][1])

        self.current_button.set_arg(newmacro)

    def schedule_macro(self, keyset):
        self.to_press = keyset
        self.after(100, self.run_macro)
        self.kill_hotkeys()

    def run_macro(self):
        if self.to_press is None:
            return
        
        for keys in self.to_press:
            keys = [key for key in keys if len(key)>0] # remove empty modifier
            keys = [Keyboard.to_pynput(key) for seq in keys for key in seq.split('+')] # split modifier and flatten
            self.keyboard.press_keys(keys) # send keypress

        self.to_press = None
        self.init_hotkeys() # restart hotkeys

    def reset_bordercols(self):
        for button in self.buttons:
            button.configure(border_color=BC_DEFAULT)

    def entryconfig(self, event):
        if isinstance(event.widget, ctk.windows.ctk_tk.CTk):
            if self.current_button is not None:
                self.current_button.configure(border_color=BC_DEFAULT)
                self.current_button = None
            self.destroy_flex()
        try:
            event.widget.focus_set()
        except AttributeError: # from color picker
            pass

    def rclick_popup(self, event, view_ix):
        self.view_edit_ix = view_ix
        self.rclickmenu.tk_popup(event.x_root, event.y_root)
        self.rclickmenu.grab_release()

    def helpertxt_clear(self):
        self.helper.configure(text='')

    def helpertxt_nobtn(self):
        self.helper.configure(text='NO BUTTON SELECTED')

    def _on_closing(self):
        self.save_data()
        self.destroy()

    ####################################
    # LAYOUT SETUP
    ####################################

    def numpad_buttongrid(self, key_layout):
        with open(key_layout, 'r') as f:
            button_mapping = json.load(f)

        buttons = []
        frame = self.topframe

        self.back_button = -1

        for i,key in enumerate(button_mapping.keys()):
            xadjustment = BUTTON_SIZES[button_mapping[key]['attr']][1]
            yadjustment = BUTTON_SIZES[button_mapping[key]['attr']][0]
            button = ActionButton(frame, 
                                #    command=mapping[key]['callback'],
                                command=partial(self.button_callback, i), 
                                text='asdf', # dummy text due to bug
                                width=85*xadjustment + 2*XPAD*(xadjustment-1),
                                height=85*yadjustment + 2*YPAD*(yadjustment-1),
                                border_width=2,
                                fg_color=FC_EMPTY,
                                hover_color=HC_EMPTY,
                                border_color=BC_DEFAULT,
                                font=self.STANDARDFONT,
                                anchor='n',
                                compound='bottom'
                                )
            button.register_actions(self._callbacks(), ACTION_ICONS)
            button.set_keys('' if button_mapping[key]['modifier'] is None else button_mapping[key]['modifier'],
                            key)
            button._text_label.configure(wraplength=WRAPLEN*xadjustment)

            # undo dummy values
            button.configure(text='')

            button.grid(row=button_mapping[key]['y'], column=button_mapping[key]['x'], 
                        padx=XPAD, pady=YPAD, 
                        rowspan=yadjustment, columnspan=xadjustment)
            button.grid_propagate(0) # prevents vertical stretching with text
            buttons.append(button)

            if button_mapping[key]['y']==0 and button_mapping[key]['x']==0:
                self.back_button=i
        
        if self.back_button<0:
            raise ValueError(f"{key_layout} missing button in top left corner (required for back button)")
        return buttons

    def button_settings(self):

        frame = self.bottomframe

        # helper text
        helper = ctk.CTkLabel(frame, text='', font=self.STANDARDFONT)
        helper.grid(row=0, column=0, columnspan=2, padx=XPAD, pady=YPAD, sticky='new')
        
        # Button Text
        txtbox = ctk.CTkEntry(frame, 
                            placeholder_text='Button Text',
                            width = XDIM/3,
                            textvariable=self.text_shared,
                            font=self.STANDARDFONT
                            )
        txtbox.grid(row=1, column=0, padx=XPAD, pady=YPAD, sticky='w')

        # Button Action
        action = ctk.CTkOptionMenu(frame, 
                                values = ACTION_VALUES,
                                command=self.set_action,
                                font=self.STANDARDFONT)
        action.grid(row=2, column=0, padx=XPAD, pady=YPAD, sticky='w')

        # Button Color
        button_clr = ctk.CTkButton(frame, 
                                command=self.choosecolor, 
                                text='Button Color',
                                font=self.STANDARDFONT)
        button_clr.grid(row=1, column=1, padx=XPAD, pady=YPAD, sticky='w')

        # Button HotKey:
        button_hkey = ctk.CTkButton(frame, 
                                    command=self.hkconfig, 
                                    text='Configure Hotkey',
                                    font=self.STANDARDFONT)
        button_hkey.grid(row=3, column=1, columnspan=1, padx=XPAD, pady=YPAD, sticky='new')

        # Button Image:
        button_img = ctk.CTkButton(frame, 
                                    command=self.imgconfig, 
                                    text='Image',
                                    font=self.STANDARDFONT)
        button_img.grid(row=3, column=0, columnspan=1, padx=XPAD, pady=YPAD, sticky='new')

        return helper, txtbox, action, button_clr

    def createViewMenu(self):
        m = tk.Menu(self, 
                    tearoff=0,
                    font=self.SMALLFONT,
                    fg='white',
                    background=FC_EMPTY,
                    activebackground='gray30',
                    bd=1,
                    relief=None
                    )
        m.add_command(label = 'Rename', command=self.rename_view1)
        m.add_separator()
        m.add_command(label = 'Delete', command=self.delete_view)

        return m

if __name__=='__main__':
    layout = 'layouts/numpad_tall.json'
    # layout = 'layouts/numpad.json'
    app = App(layout)
    ACTION_CALLS = app._callbacks()

    # initialize macros
    app.init_hotkeys()

    app.mainloop()