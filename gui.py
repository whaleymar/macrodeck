import tkinter as tk
import customtkinter as ctk
from colorpicker import AskColor, hovercolor, to_rgb # from https://github.com/Akascape/CTkColorPicker
import os
import util
import macros
from functools import partial
import json
from PIL import Image
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

def ctkimage(path, size):
    return ctk.CTkImage(Image.open(path), size=size)

####################################
# CONSTANTS
####################################

# geo
XDIM = 800
YDIM = 800 # 700 good for normal numpad
XPAD = 5
YPAD = 5

DEBUG = False

SAMPLE_TEXT=''

BUTTON_SIZES = {
    'regular':(1,1),
    'tall':(2,1),
    'wide':(1,2)
}
MODIFIERS = ['none','<ctrl>','<shift>','<alt>',
             '<ctrl>+<shift>', '<ctrl>+<alt>', 
             '<shift>+<alt>', '<ctrl>+<shift>+<alt>']
KEYS = ['<NUMPAD0>','<NUMPAD1>','<NUMPAD2>','<NUMPAD3>','<NUMPAD4>',
        '<NUMPAD5>','<NUMPAD6>','<NUMPAD7>','<NUMPAD8>','<NUMPAD9>',
        '+','-','*','/','<DECIMAL>','<RETURN>',
        '<F1>','<F2>','<F3>','<F4>','<F5>','<F6>',
        '<F7>','<F8>','<F9>','<F10>','<F11>','<F12>',
        '<F13>','<F14>','<F15>','<F16>','<F17>','<F18>',
        '<F19>','<F20>','<F21>','<F22>','<F23>','<F24>']
DEFAULT_MODIFIER = MODIFIERS[3]

ICON_SIZE = (26,23)
ACTION_VALUES = ['No Action', 'Play Media', 'Stop Media', 'Pause Media', 'Open View', 'Perform Macro', 'Open Web Page']
ACTION_ICONS = [None, ctkimage('assets/action_audio.png', ICON_SIZE), ctkimage('assets/action_mute.png', ICON_SIZE),
                ctkimage('assets/action_pause.png', ICON_SIZE),ctkimage('assets/action_openview.png', ICON_SIZE),
                ctkimage('assets/action_macro.png', ICON_SIZE), ctkimage('assets/action_web.png', ICON_SIZE)]

BACK_ICON = ctk.CTkImage(Image.open('assets/action_back.png'), size=ICON_SIZE)

BC_DEFAULT = '#565B5E' 
BC_ACTIVE = '#FFFFFF'
FC_EMPTY = '#1E1E1E'
FC_DEFAULT = '#0494D9'
HC_EMPTY = hovercolor(FC_EMPTY)
HC_DEFAULT = hovercolor(FC_DEFAULT)


WRAPLEN = 65

class App(ctk.CTk):
    def __init__(self, key_layout):
        super().__init__()

        self.geometry(f"{XDIM}x{YDIM}")
        self.STANDARDFONT = ctk.CTkFont(family='Arial', weight='bold', size=14) # default size is 13
        self.SMALLFONT = ctk.CTkFont(family='Arial', size=14) # default size is 13

        # init VLC player
        self.player = util.VLCPlayer()

        # make all widgets focus-able so I can click out of entry box:
        # also make buttons un-focusable by clicking outside of a widget
        self.bind_all("<1>", lambda event: self.entryconfig(event))

        # init right click menu for views:
        self.rclickmenu = create_menu(self)

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

        self.key_layout = os.path.basename(key_layout)[:-5] # name of layout file without extension
        self.buttons = numpad_buttongrid(self, key_layout)
        self.helper, self.txtbox, self.action, self.button_clr = button_settings(self)

        ####################################
        # IMAGES
        ####################################
        try:
            self.load_imgs()
        except (FileNotFoundError, KeyError):
            self.images = [icon for icon in ACTION_ICONS if icon is not None]

        ####################################
        # VIEWS
        ####################################

        # store empty view -- blank slate for new views
        self.empty_view = View('View 1', self.buttons)

        # load views
        self.used_colors = {FC_DEFAULT, FC_EMPTY}
        try:
            self.load_views()
        except (FileNotFoundError, KeyError):
            self.views = [self.empty_view]
        self.views[0]._main = True
        self.current_view = 0
        self.refresh_sidebar(True)
    
    # return callbacks to be used as globals
    def _callbacks(self):
        return [do_nothing, self.player.__call__, self.player.reset, self.player.toggle_pause, self.open_view, None, web.open]
    
    def init_hotkeys(self):
        self.hotkeys = macros.init_hotkeys(self.buttons) # inherits from threading.thread
        self.hotkeys.start()

    # not currently used
    def kill_hotkeys(self):
        self.hotkeys.stop()
        self.hotkeys = None
    
    def button_callback(self, button_ix):
        if self.current_button is self.buttons[button_ix]:
            self.current_button.run_action()
            return
        self.reset_bordercols()
        self.helpertxt_clear()
        self.current_button = self.buttons[button_ix]

        # set current button options in GUI:
        self.text_shared.set(self.current_button.cget("text"))
        self.current_button.configure(border_color=BC_ACTIVE)
        b_action = ACTION_VALUES[self.current_button.action_enum]
        self.action.set(b_action)
        self.set_actionbutton(b_action, False)

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

    # displays correct widget based on option menu value
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
            pass # not implemented

        elif action_text == 'Open Web Page':
            self.init_URL_entry()
            if not changed:
                self.flex_text.set(self.current_button.arg)

        else:
            raise ValueError(action_text)

    def set_action(self, action_text):
        if self.current_button is not None:
            
            # check if we are mapping a real action
            if action_text == 'No Action':
                self.current_button.deactivate()
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
                    self.current_button.set_arg(0)
                    self.current_button.set_text(str(self.views[0]), default=True)

                elif action_text == 'Perform Macro':
                    self.current_button.set_action(5)
                    pass # not implemented

                elif action_text == 'Open Web Page':
                    self.current_button.set_action(6)

                else:
                    raise ValueError(action_text)

            self.set_actionbutton(action_text, True)
            self.current_button.set_image()
        else:
            self.action.set(ACTION_VALUES[0])
            self.helpertxt_nobtn()

    # sets flex button to media
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
        self.views[self.current_view] = View(str(self.views[self.current_view]), self.buttons, ismain=self.views[self.current_view].ismain())

        # on the sidebar, highlight new view button and unhighlight old one:
        self.viewbuttons[view_enum].configure(fg_color=('gray70', 'gray30'))
        self.viewbuttons[self.current_view].configure(fg_color='transparent')

        # open new view:      
        if self.views[view_enum].ismain():
            self.buttons[self.back_button].unlock()
        self.views[view_enum].to_buttons(self.buttons, self.images)

        # handle back button & locking
        if not self.views[view_enum].ismain():
            self.buttons[self.back_button].back_button()

        self.current_view = view_enum

    # write view and image info to disk
    def save_data(self):
        # save current view:
        self.reset_bordercols()
        self.views[self.current_view] = View(str(self.views[self.current_view]), self.buttons)

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

        with open('savedata.json', 'w') as f:
            json.dump(savedata, f)
        
        print("saved data to savedata.json")

    def load_imgs(self):
        with open('savedata.json', 'r') as f:
            data = json.load(f)

        data = data['images']

        self.images = [ctkimage(elem, ICON_SIZE) for elem in data]

    def load_views(self):
        with open('savedata.json', 'r') as f:
            data = json.load(f)

        data = data['layouts'][self.key_layout]
        
        self.views = []
        for k,v in data.items():
            self.views.append(View(k, v, False))
        
        self.views[0].to_buttons(self.buttons, self.images, set_keys=True)

        # store colors
        for view in self.views:
            self.used_colors |= view.colors()

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
            win = HKWindow(self.current_button.key, self.current_button.modifier, self.STANDARDFONT)
            newkeys = win.get()
            if newkeys is None:
                return
            
            # check if this hotkey is already mapped to a different key
            oldkeys = self.current_button.get_keys() # store old keys in case we need to revert
            curhotkeys = macros.hotkeymap(self.buttons)

            self.current_button.set_keys(newkeys[0], newkeys[1])
            newhotkeys = macros.hotkeymap(self.buttons)

            if len(curhotkeys) > len(newhotkeys):
                self.helper.configure(text='KEY COMBINATION ALREADY IN USE')
                self.current_button.set_keys(oldkeys[0], oldkeys[1])
                return
            
            self.hotkeys = macros.reset_hotkeys(self.buttons, self.hotkeys)
        else:
            self.helpertxt_nobtn()

    def imgconfig(self):
        self.helpertxt_clear()
        if self.current_button is not None:
            win = IMGWindow(self.images, self.STANDARDFONT)
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
    
    def pressbutton(self): # for debugging
        if self.current_button is not None:
            self.current_button.run_action()
        else:
            self.helpertxt_nobtn()

    def reset_bordercols(self):
        for button in self.buttons:
            button.configure(border_color=BC_DEFAULT)

    def destroy_flex(self):
        if self.flex_button is not None:
            self.flex_button.destroy()
            self.flex_button = None

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
        try:
            self.rclickmenu.tk_popup(event.x_root, event.y_root)
        finally:
            self.rclickmenu.grab_release()

    def helpertxt_clear(self):
        self.helper.configure(text='')

    def helpertxt_nobtn(self):
        self.helper.configure(text='NO BUTTON SELECTED')

    def _on_closing(self):
        self.save_data()
        self.destroy()

####################################
# OOP (sksksk)
####################################

# ctk button wrapper that stores callback/args, hotkeys, and some convenience methods for main keys
class BUTTON(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.arg = None
        self.default_text = '' # if button text is empty, fill with default_text
        self.img_ix = None
        self.action_enum = 0
        self._lock = False

    def activate(self):
        # only set default color if we're coming from deactivation
        if self.cget('fg_color')==FC_EMPTY:
            self.set_colors(FC_DEFAULT, None, hovercolor(FC_DEFAULT))

    def deactivate(self):
        self.set_colors(FC_EMPTY, None, hovercolor(FC_EMPTY))
        self.default_text=''
        self.set_text('')
        self.set_action(0)
        self.set_arg(None)
        self.set_image()

    def lock(self):
        self._lock = True

    def unlock(self):
        self._lock = False

    def locked(self):
        return self._lock

    def back_button(self):
        self.unlock()
        self.deactivate()
        self.set_action(4) # open view
        self.set_arg(0) # point to main view
        self.configure(image=BACK_ICON)
        self._draw()
        self.lock()

    # stores action fxn call enum
    def set_action(self, enum):
        if self.locked():
            return
        self.action_enum = enum

    def get_action(self):
        return self.action_enum

    # stores action fxn call arg
    def set_arg(self, arg):
        if self.locked():
            return
        self.arg = arg
    
    def get_arg(self):
        return self.arg

    def set_keys(self, modifier, key):
        if modifier=='none' or modifier=='':
            self.modifier = ''
        else:
            self.modifier = modifier+'+' # add '+' for modifier for convenience
        self.key = key

    def get_keys(self):
        return self.modifier[:-1], self.key # [:-1] since we add '+' to modifier

    def set_text(self, text, default=False):
        # set button text
        # if default: sets default text attribute

        if self.locked():
            return

        # sometimes this setting gets overwritten by other ops, so resetting it here for max coverage
        if self._text_label is None:
            self.configure(text=' ')
            self.configure(text='')
            self._text_label.configure(wraplength=WRAPLEN)


        if default and self.default_text == self.cget('text'):
            # wipe default text if we are overwriting 
            self.configure(text='')

        if default:
            self.default_text=text
        else:
            self.configure(text=text[:35])
        
        if not self.cget('text') and self.default_text:
            self.configure(text=self.default_text[:35])

    def get_text(self):
        return self.cget('text'), self.default_text
    
    def set_colors(self, fg_color=None, border_color=None, hover_color=None):
        if self.locked():
            return
        
        if fg_color is not None:
            self.configure(fg_color=fg_color)
        if border_color is not None:
            self.configure(border_color=border_color)
        if hover_color is not None:
            self.configure(hover_color=hover_color)
    
    def get_colors(self):
        return self.cget('fg_color'), self.cget('border_color'), self.cget('hover_color')
    
    def set_image(self, ix=None, images=None):
        # show given image or default image if not given
        if self.locked():
            return

        self.img_ix = ix
        
        if ix is None:
            self.configure(image=ACTION_ICONS[self.action_enum])
        else:
            self.configure(image=images[ix])
        self._draw()

    def get_image(self):
        return self.img_ix

    def run_action(self):
        if self.action_enum is None: return
        if self.arg is not None:
            ACTION_CALLS[self.action_enum](self.arg)
        else:
            try:
                ACTION_CALLS[self.action_enum]()
            except TypeError:
                self.master.master.helper.configure(text='NO FILE SELECTED')
    
    # override this to stop buttons from resizing
    def _create_grid(self):
        # messing with weighting so action icon doesn't move with text
        if self._text_label is not None:
            self._text_label.grid_propagate(0)
        if self._image_label is not None:
            self.grid_rowconfigure(3, weight=1)

        if self._compound == "right":
            if self._image_label is not None:
                self._image_label.grid(row=2, column=3, sticky="w")
            if self._text_label is not None:
                self._text_label.grid(row=2, column=1, sticky="e")
        elif self._compound == "left":
            if self._image_label is not None:
                self._image_label.grid(row=2, column=1, sticky="e")
            if self._text_label is not None:
                self._text_label.grid(row=2, column=3, sticky="w")
        elif self._compound == "top":
            if self._image_label is not None:
                self._image_label.grid(row=1, column=2, sticky="s")
            if self._text_label is not None:
                self._text_label.grid(row=3, column=2, sticky="n")
        elif self._compound == "bottom":
            if self._image_label is not None:
                self._image_label.grid(row=3, column=2, pady=3, sticky="s")
            if self._text_label is not None:
                self._text_label.grid(row=0, column=2, pady=2, sticky="n")

# popup window for configuring hotkeys
class HKWindow(ctk.CTkToplevel):
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
                                          values=MODIFIERS,
                                          font=STANDARDFONT)
        self.modifier.set(modifier[:-1] if modifier !="" else MODIFIERS[0]) # we store "" instead of "none"
        
        # key: 
        self.key = ctk.CTkOptionMenu(master=self.frame,
                                     values=KEYS,
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
        self._macro = None
        self.master.wait_window(self)
        return self._macro
    
    def _ok_event(self, event=None):
        self._macro = self.modifier.get(), self.key.get()
        self.grab_release()
        self.destroy()

    def _on_closing(self):
        self._macro = None
        self.grab_release()
        self.destroy()

# popup window for configuring button image
class IMGWindow(ctk.CTkToplevel):
    def __init__(self, images, STANDARDFONT):
        super().__init__()

        imgs_per_row = 4

        WIDTH = 250
        HEIGHT=300
        self.geometry(f'{WIDTH}x{HEIGHT}')
        
        self.title("Choose Image")
        self.lift()
        self.after(10)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        self.frame = ctk.CTkFrame(master=self)
        self.frame.grid(padx=5, pady=5, sticky="nswe")

        self.sframe = ctk.CTkScrollableFrame(master=self.frame)
        self.sframe.grid(row=0, column=0, sticky='nsew')

        self.images = [img for img in images if img is not None]
        self.current_image = 0

        self.buttons = []
        for i,img in enumerate(self.images):

            button = ctk.CTkButton(
                master=self.sframe,
                width=32,
                height=32,
                fg_color=FC_EMPTY,
                hover_color=HC_EMPTY,
                border_color=BC_DEFAULT,
                command=partial(self.button_callback, i),
                image=img,
                text=''
            )
            x = i%imgs_per_row
            y = int(i/imgs_per_row)
            button.grid(row=y, column=x, padx=5, pady=5, sticky='nsew')
            self.buttons.append(button)

        self.newimg = ctk.CTkButton(master=self.frame, text="New Image", command=self.new_img)
        self.newimg.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')

        self.button = ctk.CTkButton(master=self.frame, text="OK", command=self._ok_event)
        self.button.grid(row=2, column=0, padx=5, pady=5, sticky='nsew')
        
        self.grab_set()

    def button_callback(self, ix):
        # print('pressed button', ix)
        self.current_image = ix
        self._ok_event()

    def new_img(self):
        print('getting new img')
        filetypes = (
                ('PNG files', '*.png'),
                ('All Files', '*.*')
        )

        f = tk.filedialog.askopenfilename(
            title='Choose image',
            filetypes=filetypes
        )

        if f:
            newimg = ctk.CTkImage(Image.open(f), size=ICON_SIZE)
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

# container for button grid parameters
# does not store most (c)tkinter attrs because those stay fixed
class View():
    def __init__(self, name, data, got_buttons=True, ismain=False):
        if got_buttons:
            self.configs = []
            for button in data:
                self.configs.append(
                    [button.get_action(), button.get_arg(), button.get_keys(), button.get_text(), button.get_colors(), button.get_image()]
                )
        else:
            self.configs = data
        
        self.name = name
        self._main = ismain
    
    # mutates buttons
    def to_buttons(self, buttons, images, set_keys=False):
        for config, button in zip(self.configs, buttons):
            button.default_text = config[3][1] # have to do this before set_text
            button.set_action(config[0])
            button.set_arg(config[1])

            # get image
            if config[5] is None:
                image = ACTION_ICONS[config[0]]
            else:
                image = images[config[5]]
            button.img_ix = config[5] 

            # all methods that call button.configure should go in here       
            button.configure(text=config[3][0][:35], fg_color=config[4][0], border_color=config[4][1], hover_color=config[4][2],
                             image=image)
            
            if button._text_label is None:
                button.configure(text=' ')
                button.configure(text='')
            button._text_label.configure(wraplength=WRAPLEN)

            if set_keys:
                button.set_keys(config[2][0], config[2][1]) # only do this when loading from save

    def colors(self):
        # returns set of colors used in self.configs
        # only returns fg_color (ix 1)
        return set([self.configs[i][4][0] for i in range(len(self.configs))])
    
    def ismain(self):
        return self._main
    
    def rename(self, name):
        self.name = name
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return self.name

# ctk button wrapper that stores right-click menu callback for view buttons
class ViewButton(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def set_callback(self, app, i):
        self.index = i
        self.callback = app.rclick_popup
    
    def rclick(self, event):
        self.callback(event, self.index)
    
####################################
# LAYOUT SETUP
####################################

def numpad_buttongrid(app, key_layout):
    
    with open(key_layout, 'r') as f:
        button_mapping = json.load(f)

    buttons = []
    frame = app.topframe

    app.back_button = -1

    for i,key in enumerate(button_mapping.keys()):
        xadjustment = BUTTON_SIZES[button_mapping[key]['attr']][1]
        yadjustment = BUTTON_SIZES[button_mapping[key]['attr']][0]
        button = BUTTON(frame, 
                            #    command=mapping[key]['callback'],
                               command=partial(app.button_callback, i), 
                               text='asdf', # dummy text due to bug
                               width=85*xadjustment + 2*XPAD*(xadjustment-1),
                               height=85*yadjustment + 2*YPAD*(yadjustment-1),
                               border_width=2,
                               fg_color=FC_EMPTY,
                               hover_color=HC_EMPTY,
                               border_color=BC_DEFAULT,
                               font=app.STANDARDFONT,
                               anchor='n',
                               compound='bottom'
                               )
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
            app.back_button=i
    
    if app.back_button<0:
        raise ValueError(f"{key_layout} missing button in top left corner (required for back button)")
    return buttons

def button_settings(app):

    frame = app.bottomframe

    # helper text
    helper = ctk.CTkLabel(frame, text='', font=app.STANDARDFONT)
    helper.grid(row=0, column=0, columnspan=2, padx=XPAD, pady=YPAD, sticky='new')
    
    # Button Text
    txtbox = ctk.CTkEntry(frame, 
                          placeholder_text='Button Text',
                          width = XDIM/3,
                          textvariable=app.text_shared,
                          font=app.STANDARDFONT
                          )
    txtbox.grid(row=1, column=0, padx=XPAD, pady=YPAD, sticky='w')

    # Button Action
    action = ctk.CTkOptionMenu(frame, 
                               values = ACTION_VALUES,
                               command=app.set_action,
                               font=app.STANDARDFONT)
    action.grid(row=2, column=0, padx=XPAD, pady=YPAD, sticky='w')

    # Config Button Appearance
    button_clr = ctk.CTkButton(frame, 
                               command=app.choosecolor, 
                               text='Button Color',
                               font=app.STANDARDFONT)
    button_clr.grid(row=1, column=1, padx=XPAD, pady=YPAD, sticky='w')

    # configure hotkey:
    button_hkey = ctk.CTkButton(frame, 
                                  command=app.hkconfig, 
                                  text='Configure Hotkey',
                                  font=app.STANDARDFONT)
    button_hkey.grid(row=3, column=1, columnspan=1, padx=XPAD, pady=YPAD, sticky='new')

    # configure image:
    button_img = ctk.CTkButton(frame, 
                                  command=app.imgconfig, 
                                  text='Image',
                                  font=app.STANDARDFONT)
    button_img.grid(row=3, column=0, columnspan=1, padx=XPAD, pady=YPAD, sticky='new')

    return helper, txtbox, action, button_clr

def create_menu(app):
    m = tk.Menu(app, 
                tearoff=0,
                font=app.SMALLFONT,
                fg='white',
                background=FC_EMPTY,
                activebackground='gray30',
                bd=1,
                relief=None
                )
    m.add_command(label = 'Rename', command=app.rename_view1)
    m.add_separator()
    m.add_command(label = 'Delete', command=app.delete_view)

    return m

if __name__=='__main__':
    arg1 = 'layouts/numpad_tall.json'
    # arg1 = 'layouts/numpad.json'
    app = App(arg1)
    ACTION_CALLS = app._callbacks()

    # initialize macros
    app.init_hotkeys()

    app.mainloop()