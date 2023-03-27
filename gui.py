# current state of the code is bad
# will reorg later
# sorry for using globals :-)

import tkinter as tk
import customtkinter as ctk
from collections import OrderedDict
from colorpicker import AskColor # from https://github.com/Akascape/CTkColorPicker
import os
import util
import macros

####################################
# WINDOW APPEARANCE
####################################
ctk.set_appearance_mode("System")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

####################################
# CONSTANTS
####################################

# geo
XDIM = 800
YDIM = 700
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
# STANDARDFONT = None
ACTION_VALUES = ['Play Media', 'Stop Media', 'Pause Media', 'Open Layout', 'Perform Macro']
DEFAULT_BC = "#565B5E"
DEFAULT_FC = '#0494D9'
CURRENT_BC = '#FFFFFF'
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

        ####################################
        # FRAMES
        ####################################

        # TOP:
        self.lframe = ctk.CTkFrame(self, width = (XDIM/2 - XPAD*2), height = (YDIM - YPAD*2))
        self.lframe.pack(side=tk.TOP, expand=True)

        # BOTTOM
        self.rframe = ctk.CTkFrame(self, width = (XDIM/2 - XPAD*2), height = (YDIM - YPAD*2))
        self.rframe.pack(side=tk.BOTTOM, expand=True)

        ####################################
        # GLOBALS
        ####################################

        self.text_shared = tk.StringVar(self.rframe, value='')
        self.text_shared.trace('w',self.renamebutton)

        self.current_button = None

        self.initialdir = '/' # where we start when opening a file
        self.flex_button=None

        self.buttons = numpad_buttongrid(self)
        self.helper, self.txtbox, self.action, self.button_clr = button_settings(self)
    
    # return VLC player callbacks to be used as globals
    def media_callbacks(self):
        return [self.player.__call__, self.player.reset, self.player.toggle_pause, None, None]
    
    def button_callback(self, button_ix):
        self.reset_bordercols()
        self.helpertxt_clear()
        self.current_button = self.buttons[button_ix]

        # set current button options in GUI:
        self.text_shared.set(self.current_button.cget("text"))
        self.current_button.configure(border_color=CURRENT_BC)
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
    def set_action(self, action_text):
        if self.current_button is not None:
            if action_text == 'Play Media':
                self.current_button.set_action(0)
                self.mediabutton()

            elif action_text == 'Stop Media':
                self.current_button.set_action(1)
                self.current_button.set_text('Stop Audio', default=True)
                self.text_shared.set(self.current_button.cget("text"))
                self.destroy_flex()

            elif action_text == 'Pause Media':
                self.current_button.set_action(2)
                self.current_button.set_text('Pause Audio', default=True)
                self.text_shared.set(self.current_button.cget("text"))
                self.destroy_flex()

            elif action_text == 'Open Layout':
                self.current_button.set_action(3)
                pass # not implemented

            elif action_text == 'Perform Macro':
                self.current_button.set_action(4)
                pass # not implemented

            else:
                raise ValueError(action_text)
        else:
            self.action.set(ACTION_VALUES[0])
            self.helpertxt_nobtn()

    # sets flex button to media
    def mediabutton(self):
        # display media button on rframe

        if self.flex_button is not None:
            self.destroy_flex()

        button_clr = ctk.CTkButton(self.rframe, 
                                command=self.selectfile, 
                                text='Choose File')
        button_clr.grid(row=2, column=1, padx=XPAD, pady=YPAD, sticky='w')

        self.flex_button = button_clr

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
            hover = tuple(max(col-30,0) for col in to_rgb(color))
            self.current_button.configure(hover_color='#%02x%02x%02x' % hover)
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
            oldkeys = (self.current_button.modifier, self.current_button.key) # store old keys in case we need to revert
            curhotkeys = macros.hotkeymap(self.buttons)

            self.current_button.set_keys(newkeys[0], newkeys[1])
            newhotkeys = macros.hotkeymap(self.buttons)

            if len(curhotkeys) > len(newhotkeys):
                self.helper.configure(text='KEY COMBINATION ALREADY IN USE')
                self.current_button.set_keys(oldkeys[0][:-1], oldkeys[1])
                return
            
            global hotkeys # TODO
            hotkeys = macros.reset_hotkeys(self.buttons, hotkeys)
        else:
            self.helpertxt_nobtn()
    
    def pressbutton(self): # for debugging
        if self.current_button is not None:
            self.current_button.run_action()
        else:
            self.helpertxt_nobtn()

    def reset_bordercols(self):
        for button in self.buttons:
            button.configure(border_color=DEFAULT_BC)

    def destroy_flex(self):
        if self.flex_button is not None:
            self.flex_button.destroy()
            self.flex_button = None

    def entryconfig(self, event):
        if isinstance(event.widget, ctk.windows.ctk_tk.CTk):
            if self.current_button is not None:
                self.current_button.configure(border_color=DEFAULT_BC)
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

    # dumb that I have to do this manually but eval + lambdas + fstrings wouldn't work
    # number of buttoncallbackX functions should be >= len(BUTTON_MAPPING)
    def buttoncallback0(self):
        self.button_callback(0)
    def buttoncallback1(self):
        self.button_callback(1)
    def buttoncallback2(self):
        self.button_callback(2)
    def buttoncallback3(self):
        self.button_callback(3)
    def buttoncallback4(self):
        self.button_callback(4)
    def buttoncallback5(self):
        self.button_callback(5)
    def buttoncallback6(self):
        self.button_callback(6)
    def buttoncallback7(self):
        self.button_callback(7)
    def buttoncallback8(self):
        self.button_callback(8)
    def buttoncallback9(self):
        self.button_callback(9)
    def buttoncallback10(self):
        self.button_callback(10)
    def buttoncallback11(self):
        self.button_callback(11)
    def buttoncallback12(self):
        self.button_callback(12)
    def buttoncallback13(self):
        self.button_callback(13)
    def buttoncallback14(self):
        self.button_callback(14)
    def buttoncallback15(self):
        self.button_callback(15)


####################################
# OOP (sksksk)
####################################

class BUTTON(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.arg = None
        self.default_text = '' # if button text is empty, fill with default_text
        self.action_enum = 0

    def set_action(self, enum):
        # stores action fxn call enum
        self.action_enum = enum

    def set_arg(self, arg):
        # stores action fxn call arg
        self.arg = arg

    def set_keys(self, modifier, key):
        if modifier=='none':
            self.modifier = ''
        else:
            self.modifier = modifier+'+'
        self.key = key

    def run_action(self):
        if self.action_enum is None: return
        if self.arg is not None:
            ACTION_CALLS[self.action_enum](self.arg)
        else:
            try:
                ACTION_CALLS[self.action_enum]()
            except TypeError:
                self.master.master.helper.configure(text='NO FILE SELECTED')

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

####################################
# HELPERS
####################################

def to_rgb(hexstring):
    return tuple(int(hexstring[i:i+2],16) for i in range(1,6,2))

####################################
# LAYOUT SETUP
####################################

def numpad_buttongrid(app):
    # 

    buttons = []
    frame = app.lframe

    for i,key in enumerate(BUTTON_MAPPING.keys()):
        xadjustment = BUTTON_SIZES[BUTTON_MAPPING[key]['attr']][1]
        yadjustment = BUTTON_SIZES[BUTTON_MAPPING[key]['attr']][0]
        button = BUTTON(frame, 
                            #    command=mapping[key]['callback'],
                               command=eval(f"app.buttoncallback{i}"), 
                               text='asdf',
                               width=85*xadjustment + 2*XPAD*(xadjustment-1),
                               height=85*yadjustment + 2*YPAD*(yadjustment-1),
                               border_width=2,
                               fg_color=DEFAULT_FC,
                               hover_color='#%02x%02x%02x' % tuple(max(col-30,0) for col in to_rgb(DEFAULT_FC)),
                               border_color=DEFAULT_BC,
                               font=app.STANDARDFONT)
        button.set_keys(DEFAULT_MODIFIER if BUTTON_MAPPING[key]['modifier'] is None else BUTTON_MAPPING[key]['modifier'],
                        key)
        button._text_label.configure(wraplength=WRAPLEN)
        button.configure(text='')
        button.grid(row=BUTTON_MAPPING[key]['y'], column=BUTTON_MAPPING[key]['x'], padx=XPAD, pady=YPAD, rowspan=yadjustment, columnspan=xadjustment)
        buttons.append(button)
    return buttons

def button_settings(app):

    frame = app.rframe

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
    hotkeys = macros.init_hotkeys(app.buttons) # inherits from threading.thread
    hotkeys.start()

    app.mainloop()