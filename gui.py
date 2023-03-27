# current state of the code is bad
# will reorg later
# sorry for using globals :-)

import tkinter as tk
import customtkinter as ctk
from collections import OrderedDict
from colorpicker import AskColor # from https://github.com/Akascape/CTkColorPicker
import os
from util import VLCPlayer
import macros

####################################
# WINDOW APPEARANCE
####################################
ctk.set_appearance_mode("System")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

app = ctk.CTk()  # create CTk window like you do with the Tk window
xdim = 800
ydim = 700
xpad = 5
ypad = 5
app.geometry(f"{xdim}x{ydim}")

####################################
# INIT VLC PLAYER
####################################
player = VLCPlayer()

####################################
# BUTTON CALLBACK ENUM
####################################

# dumb that I have to do this manually but eval + lambdas + fstrings wouldn't work
def buttoncallback0():
    button_callback(0)
def buttoncallback1():
    button_callback(1)
def buttoncallback2():
    button_callback(2)
def buttoncallback3():
    button_callback(3)
def buttoncallback4():
    button_callback(4)
def buttoncallback5():
    button_callback(5)
def buttoncallback6():
    button_callback(6)
def buttoncallback7():
    button_callback(7)
def buttoncallback8():
    button_callback(8)
def buttoncallback9():
    button_callback(9)
def buttoncallback10():
    button_callback(10)
def buttoncallback11():
    button_callback(11)
def buttoncallback12():
    button_callback(12)
def buttoncallback13():
    button_callback(13)
def buttoncallback14():
    button_callback(14)
def buttoncallback15():
    button_callback(15)

####################################
# CONSTANTS
####################################

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
        'callback':buttoncallback0,
        'modifier':None
    },
    '<NUMPAD1>':{
        'x':0,
        'y':3,
        'attr':'regular',
        'callback':buttoncallback1,
        'modifier':None
    },
    '<NUMPAD2>':{
        'x':1,
        'y':3,
        'attr':'regular',
        'callback':buttoncallback2,
        'modifier':None
    },
    '<NUMPAD3>':{
        'x':2,
        'y':3,
        'attr':'regular',
        'callback':buttoncallback3,
        'modifier':None
    },
    '<NUMPAD4>':{
        'x':0,
        'y':2,
        'attr':'regular',
        'callback':buttoncallback4,
        'modifier':None
    },
    '<NUMPAD5>':{
        'x':1,
        'y':2,
        'attr':'regular',
        'callback':buttoncallback5,
        'modifier':None
    },
    '<NUMPAD6>':{
        'x':2,
        'y':2,
        'attr':'regular',
        'callback':buttoncallback6,
        'modifier':None
    },
    '<NUMPAD7>':{
        'x':0,
        'y':1,
        'attr':'regular',
        'callback':buttoncallback7,
        'modifier':None
    },
    '<NUMPAD8>':{
        'x':1,
        'y':1,
        'attr':'regular',
        'callback':buttoncallback8,
        'modifier':None
    },
    '<NUMPAD9>':{
        'x':2,
        'y':1,
        'attr':'regular',
        'callback':buttoncallback9,
        'modifier':None
    },
    '<DECIMAL>':{
        'x':2,
        'y':4,
        'attr':'regular',
        'callback':buttoncallback10,
        'modifier':None
    },
    '<RETURN>':{
        'x':3,
        'y':3,
        'attr':'tall',
        'callback':buttoncallback11,
        'modifier':None
    },
    '+':{
        'x':3,
        'y':1,
        'attr':'tall',
        'callback':buttoncallback12,
        'modifier':None
    },
    '-':{
        'x':3,
        'y':0,
        'attr':'regular',
        'callback':buttoncallback13,
        'modifier':None
    },
    '*':{
        'x':2,
        'y':0,
        'attr':'regular',
        'callback':buttoncallback14,
        'modifier':None
    },
    '/':{
        'x':1,
        'y':0,
        'attr':'regular',
        'callback':buttoncallback15,
        'modifier':None
    }
})

ACTION_VALUES = ['Play Media', 'Stop Media', 'Pause Media', 'Open Layout', 'Perform Macro']
ACTION_CALLS = [player.__call__, player.reset, player.toggle_pause, None, None]
DEFAULT_BC = "#565B5E"
DEFAULT_FC = '#0494D9'
CURRENT_BC = '#FFFFFF'
WRAPLEN = 65
STANDARDFONT = ctk.CTkFont(family='Arial', weight='bold', size=14) # default size is 13




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
                helper.configure(text='NO FILE SELECTED')

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
    def __init__(self, key, modifier):
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
# CALLBACKS
####################################
def button_callback(button_ix):
    reset_bordercols()
    helpertxt_clear()
    global current_button
    current_button = buttons[button_ix]

    # set current button options in GUI:
    buttontext_shared.set(current_button.cget("text"))
    current_button.configure(border_color=CURRENT_BC)
    b_action = ACTION_VALUES[current_button.action_enum]
    action.set(b_action)
    set_action(b_action)

# sets flex button to media
def mediabutton():
    # display media button on rframe
    # should become rframe class method
    global flex_button

    if flex_button is not None:
        destroy_flex()

    button_clr = ctk.CTkButton(rframe, 
                               command=selectfile, 
                               text='Choose File')
    button_clr.grid(row=2, column=1, padx=xpad, pady=ypad, sticky='w')

    flex_button = button_clr

def selectfile():
    global initialdir
    helpertxt_clear() # in case there is a "NO FILE SELECTED" message
    if current_button is not None:
        filetypes = (
            ('MP3 files', '*.mp3'),
            ('All Files', '*.*')
        )

        f = tk.filedialog.askopenfilename(
            title='Choose song',
            initialdir=initialdir,
            filetypes=filetypes
        )
        
        if f:
            initialdir = os.path.dirname(f) # remember dir we used

            # configure button text
            current_button.set_text(os.path.basename(f).split('.')[0], default=True)
            buttontext_shared.set(current_button.cget("text")) # re-fill entry text in case it changed

            # set button action and arg
            current_button.set_arg(f)
    else:
        helpertxt_nobtn()

def set_action(action_text):
    # displays correct button based on option menu value
    # current options: ['Play Media', 'Stop Media', 'Open Layout', 'Perform Macro']

    if current_button is not None:
        if action_text == 'Play Media':
            current_button.set_action(0)
            mediabutton()
        elif action_text == 'Stop Media':
            current_button.set_action(1)
            current_button.set_text('Stop Audio', default=True)
            buttontext_shared.set(current_button.cget("text"))
            destroy_flex()
        elif action_text == 'Pause Media':
            current_button.set_action(2)
            current_button.set_text('Pause Audio', default=True)
            buttontext_shared.set(current_button.cget("text"))
            destroy_flex()
        elif action_text == 'Open Layout':
            current_button.set_action(3)
            pass # not implemented
        elif action_text == 'Perform Macro':
            current_button.set_action(4)
            pass # not implemented
        else:
            raise ValueError(action_text)
    else:
        action.set(ACTION_VALUES[0])
        helpertxt_nobtn()

def choosecolor():
    if current_button is not None:
        # get current color to initialize window
        current_color = current_button.cget('fg_color')
        if len(current_color)==2: current_color=current_color[1] # dark theme color is second
        current_color = to_rgb(current_color)
        pick_color = AskColor(color = current_color)
        color = pick_color.get()
        if color is None:
            # exited without choosing a color
            return
        current_button.configure(fg_color=color)
        hover = tuple(max(col-30,0) for col in to_rgb(color))
        current_button.configure(hover_color='#%02x%02x%02x' % hover)
    else:
        helpertxt_nobtn()

def renamebutton(*args): # args has metadata on the variable who called us
    
    if current_button is not None:
        current_button.set_text(buttontext_shared.get())
    else:
        helpertxt_nobtn()

def hkconfig():
    global hotkeys
    helpertxt_clear()
    if current_button is not None:
        win = HKWindow(current_button.key, current_button.modifier)
        newkeys = win.get()
        if newkeys is None:
            return
        
        # check if this hotkey is already mapped to a different key
        oldkeys = (current_button.modifier, current_button.key) # store old keys in case we need to revert
        curhotkeys = macros.hotkeymap(buttons)

        current_button.set_keys(newkeys[0], newkeys[1])
        newhotkeys = macros.hotkeymap(buttons)

        if len(curhotkeys) > len(newhotkeys):
            helper.configure(text='KEY COMBINATION ALREADY IN USE')
            current_button.set_keys(oldkeys[0][:-1], oldkeys[1])
            return
        
        hotkeys = macros.reset_hotkeys(buttons, hotkeys)
    else:
        helpertxt_nobtn()

def pressbutton(): # for debugging
    if current_button is not None:
        current_button.run_action()
    else:
        helpertxt_nobtn()

####################################
# HELPERS
####################################

def reset_bordercols():
    global buttons
    for button in buttons:
        button.configure(border_color=DEFAULT_BC)

def helpertxt_clear():
    helper.configure(text='')

def helpertxt_nobtn():
    helper.configure(text='NO BUTTON SELECTED')

def to_rgb(hexstring):
    return tuple(int(hexstring[i:i+2],16) for i in range(1,6,2))

def destroy_flex():
    global flex_button
    if flex_button is not None:
        flex_button.destroy()
        flex_button = None

def entryconfig(event):
    global current_button
    if isinstance(event.widget, ctk.windows.ctk_tk.CTk):
        if current_button is not None:
            current_button.configure(border_color=DEFAULT_BC)
            current_button = None
        destroy_flex()
    try:
        event.widget.focus_set()
    except AttributeError: # from color picker
        pass

####################################
# LAYOUT SETUP
####################################

def numpad_buttongrid(frame, mapping):
    # 

    buttons = []
    callbacks = []
    # frame.grid_rowconfigure(4,weight=1)
    # frame.grid_columnconfigure(0,weight=1)
    for i,key in enumerate(mapping.keys()):
        xadjustment = BUTTON_SIZES[mapping[key]['attr']][1]
        yadjustment = BUTTON_SIZES[mapping[key]['attr']][0]
        button = BUTTON(frame, 
                            #    command=mapping[key]['callback'],
                               command=mapping[key]['callback'], 
                               text='asdf',
                               width=85*xadjustment + 2*xpad*(xadjustment-1),
                               height=85*yadjustment + 2*ypad*(yadjustment-1),
                               border_width=2,
                               fg_color=DEFAULT_FC,
                               hover_color='#%02x%02x%02x' % tuple(max(col-30,0) for col in to_rgb(DEFAULT_FC)),
                               border_color=DEFAULT_BC,
                               font=STANDARDFONT)
        button.set_keys(DEFAULT_MODIFIER if mapping[key]['modifier'] is None else mapping[key]['modifier'],
                        key)
        button._text_label.configure(wraplength=WRAPLEN)
        button.configure(text='')
        button.grid(row=mapping[key]['y'], column=mapping[key]['x'], padx=xpad, pady=ypad, rowspan=yadjustment, columnspan=xadjustment)
        buttons.append(button)
    return buttons

def button_settings(frame):
    # frame.grid_rowconfigure(4,weight=1)
    # frame.grid_columnconfigure(4,weight=1)

    # helper text
    helper = ctk.CTkLabel(frame, text='', font=STANDARDFONT)
    helper.grid(row=0, column=0, columnspan=2, padx=xpad, pady=ypad, sticky='new')
    
    # Button Text
    txtbox = ctk.CTkEntry(frame, 
                          placeholder_text='Button Text',
                          width = xdim/3,
                          textvariable=buttontext_shared
                          )
    txtbox.grid(row=1, column=0, padx=xpad, pady=ypad, sticky='w')

    # Button Action
    action = ctk.CTkOptionMenu(frame, 
                               values = ACTION_VALUES,
                               command=set_action)
    action.grid(row=2, column=0, padx=xpad, pady=ypad, sticky='w')

    # Config Button Appearance
    button_clr = ctk.CTkButton(frame, 
                               command=choosecolor, 
                               text='Button Color')
    button_clr.grid(row=1, column=1, padx=xpad, pady=ypad, sticky='w')

    # configure hotkey:
    button_hkey = ctk.CTkButton(frame, 
                                  command=hkconfig, 
                                  text='Configure Hotkey')
    button_hkey.grid(row=3, column=0, columnspan=2, padx=xpad, pady=ypad, sticky='new')

    # button to simulate key press (for debugging)
    if DEBUG:
        button_kpress = ctk.CTkButton(frame, 
                               command=pressbutton, 
                               text='Simulate Key Press')
        button_kpress.grid(row=4, column=0, columnspan=2, padx=xpad, pady=ypad, sticky='new')

    return helper, txtbox, action, button_clr


####################################
# GLOBALS
####################################


# set up left side:
lframe = ctk.CTkFrame(app, width = (xdim/2 - xpad*2), height = (ydim - ypad*2))
# lframe.grid(row=0, column=0, rowspan=4, sticky='sw')
lframe.pack(side=tk.TOP, expand=True)
buttons = numpad_buttongrid(lframe, BUTTON_MAPPING)

# set up right side
rframe = ctk.CTkFrame(app, width = (xdim/2 - xpad*2), height = (ydim - ypad*2))
rframe.pack(side=tk.BOTTOM, expand=True)

buttontext_shared = tk.StringVar(rframe, value='')
buttontext_shared.trace('w',renamebutton)

current_button = None

initialdir = '/'
flex_button=None

helper, txtbox, action, button_clr = button_settings(rframe)

# make all widgets focus-able so I can click out of entry box:
# also make buttons un-focusable by clicking outside of a widget
app.bind_all("<1>", lambda event: entryconfig(event))

# initialize macros
hotkeys = macros.init_hotkeys(buttons) # inherits from threading.thread
hotkeys.start()

app.mainloop()