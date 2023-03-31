import tkinter as tk
import customtkinter as ctk
from collections import OrderedDict
from colorpicker import AskColor # from https://github.com/Akascape/CTkColorPicker
import os
import util
import macros
from functools import partial
import time
import json
# from multiprocessing import Queue # communication btwn threads
# import threading

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

def hovercolor(hexstring):
    return '#%02x%02x%02x' % tuple(max(col-30,0) for col in to_rgb(hexstring))

def to_rgb(hexstring):
    return tuple(int(hexstring[i:i+2],16) for i in range(1,6,2))


####################################
# CONSTANTS
####################################

# geo
XDIM = 800
YDIM = 700
XPAD = 5
YPAD = 5

DEBUG = True

SAMPLE_TEXT=''

BUTTON_SIZES = {
    'regular':(1,1),
    'tall':(2,1),
    'wide':(1,2)
}
MODIFIERS = ['none','<ctrl>','<shift>','<alt>',
             '<ctrl>+<shift>', '<ctrl>+<alt>', 
             '<shift>+<alt>', '<ctrl>+<shift>+<alt>']
DEFAULT_MODIFIER = MODIFIERS[3]

# note: y=0 is top of grid
BUTTON_MAPPING = OrderedDict({
    '<NUMPAD0>': {
        'x':0,
        'y':4,
        'attr':'wide',
        'modifier':None
    },
    '<NUMPAD1>':{
        'x':0,
        'y':3,
        'attr':'regular',
        'modifier':None
    },
    '<NUMPAD2>':{
        'x':1,
        'y':3,
        'attr':'regular',
        'modifier':None
    },
    '<NUMPAD3>':{
        'x':2,
        'y':3,
        'attr':'regular',
        'modifier':None
    },
    '<NUMPAD4>':{
        'x':0,
        'y':2,
        'attr':'regular',
        'modifier':None
    },
    '<NUMPAD5>':{
        'x':1,
        'y':2,
        'attr':'regular',
        'modifier':None
    },
    '<NUMPAD6>':{
        'x':2,
        'y':2,
        'attr':'regular',
        'modifier':None
    },
    '<NUMPAD7>':{
        'x':0,
        'y':1,
        'attr':'regular',
        'modifier':None
    },
    '<NUMPAD8>':{
        'x':1,
        'y':1,
        'attr':'regular',
        'modifier':None
    },
    '<NUMPAD9>':{
        'x':2,
        'y':1,
        'attr':'regular',
        'modifier':None
    },
    '<DECIMAL>':{
        'x':2,
        'y':4,
        'attr':'regular',
        'modifier':None
    },
    '<RETURN>':{
        'x':3,
        'y':3,
        'attr':'tall',
        'modifier':None
    },
    '+':{
        'x':3,
        'y':1,
        'attr':'tall',
        'modifier':None
    },
    '-':{
        'x':3,
        'y':0,
        'attr':'regular',
        'modifier':None
    },
    '*':{
        'x':2,
        'y':0,
        'attr':'regular',
        'modifier':None
    },
    '/':{
        'x':1,
        'y':0,
        'attr':'regular',
        'modifier':None
    }
})

ACTION_VALUES = ['No Action', 'Play Media', 'Stop Media', 'Pause Media', 'Open Layout', 'Perform Macro']

BC_DEFAULT = '#565B5E' 
BC_ACTIVE = '#FFFFFF'
FC_EMPTY = '#1E1E1E'
FC_DEFAULT = '#0494D9'
HC_EMPTY = hovercolor(FC_EMPTY)
HC_DEFAULT = hovercolor(FC_DEFAULT)


WRAPLEN = 65

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.geometry(f"{XDIM}x{YDIM}")
        self.STANDARDFONT = ctk.CTkFont(family='Arial', weight='bold', size=14) # default size is 13

        # init VLC player
        self.player = util.VLCPlayer()

        # make all widgets focus-able so I can click out of entry box:
        # also make buttons un-focusable by clicking outside of a widget
        self.bind_all("<1>", lambda event: self.entryconfig(event))

        # save layouts on closing:
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        ####################################
        # FRAMES
        ####################################

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # BOTTOM (button settings)
        self.bottomframe = ctk.CTkFrame(self, width = (XDIM/2 - XPAD*2), height = (YDIM - YPAD*2))
        self.bottomframe.grid(row=1, column=1, sticky='')

        # LEFT SIDEBAR (layout selection)
        self.lframe = ctk.CTkScrollableFrame(self, corner_radius=0, height=YDIM)
        self.lframe.grid(row=0, column=0, rowspan=2, sticky='nsew')
        self.lframe.grid_columnconfigure(0,weight=1)
        self.newlayoutbutton = ctk.CTkButton(self.lframe, corner_radius=0, height=40, border_spacing=10,
                                                text="New Layout", 
                                                font=self.STANDARDFONT,
                                                anchor='w', command=self.new_layout)
        self.newlayoutbutton.grid(row=0, column=0, sticky='ew')
        self.rmlayoutbutton = ctk.CTkButton(self.lframe, corner_radius=0, height=40, border_spacing=10,
                                                text="Delete Layout", 
                                                font=self.STANDARDFONT,
                                                fg_color='#da0704',
                                                hover_color=hovercolor('#ff4542'),
                                                anchor='w', command=self.delete_layout)
        self.rmlayoutbutton.grid(row=1, column=0, sticky='ew')

        # TOP (button grid)
        self.topframe = ctk.CTkFrame(self, width = (XDIM/2 - XPAD*2), height = (YDIM - YPAD*2))
        self.topframe.grid(row=0, column=1, sticky='')


        ####################################
        # GLOBALS
        ####################################

        self.text_shared = tk.StringVar(self.bottomframe, value='')
        self.text_shared.trace('w',self.renamebutton)

        self.current_button = None

        self.initialdir = '/' # where we start when opening a file
        self.flex_button=None

        self.buttons = numpad_buttongrid(self)
        self.helper, self.txtbox, self.action, self.button_clr = button_settings(self)

        ####################################
        # PROFILES
        ####################################

        # store empty profile for creating new ones
        self.empty_profile = Layout('Layout 1', self.buttons)

        # load layouts
        try:
            self.load_layouts()
        except FileNotFoundError:
            self.layouts = [self.empty_profile]
        self.layouts[0]._main = True
        self.current_layout = 0
        self.refresh_sidebar(True)

        ####################################
        # THREADS
        ####################################
        # create worker + queue to handle layout switching
        # this is necessary since the hotkey thread is reset during a layout switch
        # self.q_layout = Queue() # FIFO
        # self.layout_thread = threading.Thread(target=self.layout_worker, daemon=True, name="layout")
        # self.layout_thread.start()

    
    # return VLC player callbacks to be used as globals
    def media_callbacks(self):
        return [do_nothing, self.player.__call__, self.player.reset, self.player.toggle_pause, self.open_layout, None]
    
    def init_hotkeys(self):
        self.hotkeys = macros.init_hotkeys(self.buttons) # inherits from threading.thread
        self.hotkeys.start()

    # def kill_hotkeys(self):
    #     self.hotkeys.stop()
    #     self.hotkeys = None
    
    def button_callback(self, button_ix):
        self.reset_bordercols()
        self.helpertxt_clear()
        self.current_button = self.buttons[button_ix]

        # set current button options in GUI:
        self.text_shared.set(self.current_button.cget("text"))
        self.current_button.configure(border_color=BC_ACTIVE)
        b_action = ACTION_VALUES[self.current_button.action_enum]
        self.action.set(b_action)
        self.set_action(b_action)

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

    # displays correct button based on option menu value
    def set_actionbutton(self, action_text):
        self.text_shared.set(self.current_button.cget("text"))

        if action_text == 'No Action':
            self.destroy_flex()
        
        elif action_text == 'Play Media':
            self.mediabutton()

        elif action_text == 'Stop Media':
            self.destroy_flex()

        elif action_text == 'Pause Media':
            self.destroy_flex()

        elif action_text == 'Open Layout':
            self.init_layoutbutton()

        elif action_text == 'Perform Macro':
            pass # not implemented

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

                elif action_text == 'Open Layout':
                    self.current_button.set_action(4)
                    self.current_button.set_text(self.current_button.arg, default=True)

                elif action_text == 'Perform Macro':
                    self.current_button.set_action(5)
                    pass # not implemented

                else:
                    raise ValueError(action_text)

            self.set_actionbutton(action_text)
        else:
            self.action.set(ACTION_VALUES[0])
            self.helpertxt_nobtn()

    # sets flex button to media
    def mediabutton(self):
        # display media button on bottomframe

        self.destroy_flex()

        button_clr = ctk.CTkButton(self.bottomframe, 
                                command=self.selectfile, 
                                text='Choose File')
        button_clr.grid(row=2, column=1, padx=XPAD, pady=YPAD, sticky='w')

        self.flex_button = button_clr

    # sets flex button to layout optionmenu
    def init_layoutbutton(self):
        # display media button on bottomframe

        self.destroy_flex()
        layouts = [str(l) for l in self.layouts]

        button_layout = ctk.CTkOptionMenu(self.bottomframe,
                                command=self.arg_from_options, 
                                values=layouts)
        # button identity not new
        if self.current_button.arg in layouts:
            button_layout.set(self.current_button.arg)

        # set button default text
        self.arg_from_options(button_layout.get())

        button_layout.grid(row=2, column=1, padx=XPAD, pady=YPAD, sticky='w')

        self.flex_button = button_layout

    def new_layout(self):
        # reset active button
        if self.current_button is not None:
                self.current_button.configure(border_color=BC_DEFAULT)
                self.current_button = None

        self.destroy_flex()
        # self.layouts.append(Layout(f'Layout {len(self.layouts)+1}', self.buttons)) # copy current layout
        
        # append empty layout
        self.layouts.append(Layout(f'Layout {len(self.layouts)+1}', self.empty_profile.configs, False))
        self.refresh_sidebar()

    def delete_layout(self):
        if self.layouts[self.current_layout].ismain():
            self.helper.configure(text='CANNOT DELETE MAIN PROFILE')
        else:
            to_delete = self.current_layout
            self.switch_layout(to_delete-1)
            self.layouts.pop(to_delete)
            # self.layoutbuttons[to_delete].destroy()
            self.refresh_sidebar()

    def open_layout(self, layout_name):
        layout_enum = -1
        for i in range(len(self.layouts)):
            if str(self.layouts[i]) == layout_name:
                layout_enum = i
                break

        if layout_enum == -1:
            raise ValueError(layout_name)
        
        # self.switch_layout(layout_enum)
        # self.q_layout.put(layout_enum) # tell worker to switch layouts

        # kill hotkey thread before we mutate the buttons
        # self.kill_hotkeys()

        self.switch_layout(layout_enum)

    def switch_layout(self, layout_enum):

        # reset active buttons
        if self.current_button is not None:
                self.current_button.configure(border_color=BC_DEFAULT)
                self.current_button = None
        self.destroy_flex()
        
        if layout_enum == self.current_layout: return

        # save current layout:
        self.layouts[self.current_layout] = Layout(str(self.layouts[self.current_layout]), self.buttons, ismain=self.layouts[self.current_layout].ismain())

        # on the sidebar, highlight new layout button and unhighlight old one:
        self.layoutbuttons[layout_enum].configure(fg_color=('gray70', 'gray30'))
        self.layoutbuttons[self.current_layout].configure(fg_color='transparent')

        # open new layout:      
        self.current_layout = layout_enum
        self.layouts[self.current_layout].to_buttons(self.buttons)
        # print(f'switched to layout {layout_enum+1}')

        # re-init hotkeys
        # self.init_hotkeys()

    # write all layout info to disk
    def save_layouts(self):#, layout_enum):
        # save current layout:
        self.reset_bordercols()
        self.layouts[self.current_layout] = Layout(str(self.layouts[self.current_layout]), self.buttons)

        data = {}
        for layout in self.layouts:
            data[str(layout)] = layout.configs
        with open('savedata.json', 'w') as f:
            json.dump(data, f)
        
        print("saved layouts to savedata.json")

    def load_layouts(self):
        with open('savedata.json', 'r') as f:
            data = json.load(f)
        
        self.layouts = []
        for k,v in data.items():
            self.layouts.append(Layout(k, v, False))
        
        self.layouts[0].to_buttons(self.buttons)

    def refresh_sidebar(self, init=False):
        if not init:
            for button in self.layoutbuttons:
                button.destroy()
        self.layoutbuttons = []
        for i,layout in enumerate(self.layouts):
            fg_color = ('gray70', 'gray30') if i==self.current_layout else 'transparent'
            newbutton = ctk.CTkButton(self.lframe, corner_radius=0, height=40, border_spacing=10,
                                      text=str(layout), fg_color=fg_color, 
                                      font=self.STANDARDFONT, hover_color=('gray70', 'gray30'),
                                      anchor='w', 
                                      command=partial(self.switch_layout,i)
                                      )
            newbutton.grid(row=i+2, column=0, sticky='ew') # +2 for new layout and remove buttons
            self.layoutbuttons.append(newbutton)

    # sets arg and defaulttext of current button (currently used for layout action)
    def arg_from_options(self, arg):
        self.current_button.set_arg(arg)
        self.current_button.set_text(arg, default=True)

    def choosecolor(self):
        if self.current_button is not None:
            # get current color to initialize window
            current_color = self.current_button.cget('fg_color')
            if len(current_color)==2: current_color=current_color[1] # dark theme color is second
            current_color = to_rgb(current_color)
            pick_color = AskColor(color = current_color)
            color = pick_color.get()
            if color is None:
                # exited without choosing a color
                return
            self.current_button.configure(fg_color=color)
            self.current_button.configure(hover_color=hovercolor(color))
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

    def helpertxt_clear(self):
        self.helper.configure(text='')

    def helpertxt_nobtn(self):
        self.helper.configure(text='NO BUTTON SELECTED')

    def layout_worker(self):
        while True:
            if self.q_layout.empty():
                # time.sleep(0.5)
                continue
            layout_enum = self.q_layout.get()
            self.switch_layout(layout_enum)
            time.sleep(0.1)

    def _on_closing(self):
        self.save_layouts()
        self.destroy()

####################################
# OOP (sksksk)
####################################

class BUTTON(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.arg = None
        self.default_text = '' # if button text is empty, fill with default_text
        self.action_enum = 0

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

    # stores action fxn call enum
    def set_action(self, enum):
        self.action_enum = enum

    def get_action(self):
        return self.action_enum

    # stores action fxn call arg
    def set_arg(self, arg):
        self.arg = arg
    
    def get_arg(self):
        return self.arg

    def set_keys(self, modifier, key):
        if modifier=='none':
            self.modifier = ''
        else:
            self.modifier = modifier+'+' # add '+' for modifier for convenience
        self.key = key

    def get_keys(self):
        return self.modifier[:-1], self.key # [:-1] since we add '+' to modifier

    def set_text(self, text, default=False):
        # set button text
        # if default: sets default text attribute

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
        if fg_color is not None:
            self.configure(fg_color=fg_color)
        if border_color is not None:
            self.configure(border_color=border_color)
        if hover_color is not None:
            self.configure(hover_color=hover_color)
    
    def get_colors(self):
        return self.cget('fg_color'), self.cget('border_color'), self.cget('hover_color')

    def run_action(self):
        if self.action_enum is None: return
        if self.arg is not None:
            ACTION_CALLS[self.action_enum](self.arg)
        else:
            try:
                ACTION_CALLS[self.action_enum]()
            except TypeError:
                self.master.master.helper.configure(text='NO FILE SELECTED')

class HKWindow(ctk.CTkToplevel):
    def __init__(self, key, modifier, STANDARDFONT):
        super().__init__()
        WIDTH = 350
        HEIGHT=250
        self.geometry(f'{WIDTH}x{HEIGHT}')
        
        self.title("Choose Color")
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
        self.modifier.set(modifier[:-1])
        # key: 
        # I know it's a forward slash but pynput makes the rules
        self.key = ctk.CTkOptionMenu(master=self.frame,
                                     values=list(BUTTON_MAPPING.keys()),
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

# container for button grid parameters
# does not store most (c)tkinter attrs because those stay fixed
class Layout():
    def __init__(self, name, data, got_buttons=True, ismain=False):
        if got_buttons:
            self.configs = []
            for button in data:
                self.configs.append(
                    [button.get_action(), button.get_arg(), button.get_keys(), button.get_text(), button.get_colors()]
                )
        else:
            self.configs = data
        
        self.name = name
        self._main = ismain
    
    # mutates buttons
    def to_buttons(self, buttons):
        for config, button in zip(self.configs, buttons):
            button.default_text = config[3][1] # have to do this before set_text
            button.set_text(config[3][0])
            button.set_action(config[0])
            button.set_arg(config[1])
            button.set_colors(config[4][0], config[4][1], config[4][2])
            # button.set_keys(config[2][0], config[2][1]) # doing this seems confusing
    
    def ismain(self):
        return self._main
    
    def __str__(self):
        return self.__repr__()
    
    def __repr__(self):
        return self.name

####################################
# LAYOUT SETUP
####################################

def numpad_buttongrid(app):
    # 

    buttons = []
    frame = app.topframe

    for i,key in enumerate(BUTTON_MAPPING.keys()):
        xadjustment = BUTTON_SIZES[BUTTON_MAPPING[key]['attr']][1]
        yadjustment = BUTTON_SIZES[BUTTON_MAPPING[key]['attr']][0]
        button = BUTTON(frame, 
                            #    command=mapping[key]['callback'],
                               command=partial(app.button_callback, i), 
                               text='asdf',
                               width=85*xadjustment + 2*XPAD*(xadjustment-1),
                               height=85*yadjustment + 2*YPAD*(yadjustment-1),
                               border_width=2,
                               fg_color=FC_EMPTY,
                               hover_color=HC_EMPTY,
                               border_color=BC_DEFAULT,
                               font=app.STANDARDFONT,
                               )
        button.set_keys(DEFAULT_MODIFIER if BUTTON_MAPPING[key]['modifier'] is None else BUTTON_MAPPING[key]['modifier'],
                        key)
        button._text_label.configure(wraplength=WRAPLEN)
        button.configure(text='')
        button.grid(row=BUTTON_MAPPING[key]['y'], column=BUTTON_MAPPING[key]['x'], 
                    padx=XPAD, pady=YPAD, 
                    rowspan=yadjustment, columnspan=xadjustment)
        buttons.append(button)
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
                          textvariable=app.text_shared
                          )
    txtbox.grid(row=1, column=0, padx=XPAD, pady=YPAD, sticky='w')

    # Button Action
    action = ctk.CTkOptionMenu(frame, 
                               values = ACTION_VALUES,
                               command=app.set_action)
    action.grid(row=2, column=0, padx=XPAD, pady=YPAD, sticky='w')

    # Config Button Appearance
    button_clr = ctk.CTkButton(frame, 
                               command=app.choosecolor, 
                               text='Button Color')
    button_clr.grid(row=1, column=1, padx=XPAD, pady=YPAD, sticky='w')

    # configure hotkey:
    button_hkey = ctk.CTkButton(frame, 
                                  command=app.hkconfig, 
                                  text='Configure Hotkey')
    button_hkey.grid(row=3, column=0, columnspan=2, padx=XPAD, pady=YPAD, sticky='new')

    # button to simulate key press (for debugging)
    if DEBUG:
        button_kpress = ctk.CTkButton(frame, 
                               command=app.pressbutton, 
                               text='Simulate Key Press')
        button_kpress.grid(row=4, column=0, columnspan=2, padx=XPAD, pady=YPAD, sticky='new')

    return helper, txtbox, action, button_clr


if __name__=='__main__':
    app = App()
    ACTION_CALLS = app.media_callbacks()

    # initialize macros
    app.init_hotkeys()

    app.mainloop()