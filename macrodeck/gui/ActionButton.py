import customtkinter as ctk
from macrodeck.gui.style import FC_DEFAULT, FC_DEFAULT2, FC_EMPTY, WRAPLEN, ICON_SIZE
from macrodeck.gui.util import hovercolor, ctkimage

BACK_ICON = ctkimage('assets/action_back.png', size=ICON_SIZE)

# ctk button wrapper that stores callback/args, hotkeys, and some convenience methods for main keys
class ActionButton(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.arg = None
        self.default_text = '' # if button text is empty, fill with default_text
        self.img_ix = None
        self.action_enum = 0
        self._lock = False
        self._global = False

        
        self.ACTION_ICONS = None
        self.ACTION_CALLS = None

    def register_actions(self, calls, icons):
        self.ACTION_ICONS = icons
        self.ACTION_CALLS = calls

    def activate(self):
        # only set default color if we're coming from deactivation
        if self.cget('fg_color')==FC_EMPTY:
            if self.grid_info()['row']%2==0:
                col = FC_DEFAULT
            else:
                col = FC_DEFAULT2
            self.set_colors(col, None, hovercolor(col))

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
            self.configure(image=self.ACTION_ICONS[self.action_enum])
        else:
            self.configure(image=images[ix])
        self._draw()

    def get_image(self):
        return self.img_ix

    def run_action(self):
        if self.action_enum is None: return
        if self.arg is not None:
            self.ACTION_CALLS[self.action_enum](self.arg)
        else:
            try:
                self.ACTION_CALLS[self.action_enum]()
            except TypeError:
                self.master.master.helper.configure(text='Error: Button Not Configured')
    
    def dump(self):
        return [self.get_action(), self.get_arg(), self.get_keys(), self.get_text(), self.get_colors(), self.get_image()]

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
