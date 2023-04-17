import customtkinter as ctk
from macrodeck.gui.style import WRAPLEN

# container for button grid data
# facilitates writing/reading from save data
# does not store most (c)tkinter attrs because those stay fixed
class View():
    def __init__(self, name, data, got_buttons=True, ismain=False):
        if got_buttons:
            self.configs = []
            for button in data:
                self.configs.append(button.dump())
        else:
            self.configs = [elem[:] for elem in data]
        
        self.name = name
        self._main = ismain
    
    # mutates buttons
    def to_buttons(self, buttons, images, action_icons, set_keys=False):
        for config, button in zip(self.configs, buttons):
            # don't change button if global
            if button._global:
                if self.ismain():
                    button.unlock()
                else:
                    button.lock()
                continue

            button.default_text = config[3][1] # have to do this before set_text
            button.set_action(config[0])
            button.set_arg(config[1])

            # get image
            if config[5] is None:
                image = action_icons[config[0]]
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

    def update(self, buttons):
        # assert len(self.configs) == len(buttons)
        for i in range(len(self.configs)):
            button = buttons[i]
            if button._global:
                if self.ismain():
                    self.configs[i] = button.dump()
                    button.lock()
                else:
                    pass
            else:
                self.configs[i] = button.dump()

    def swap_views(self, i, j):
        """
        if any button's action is to Open View i, switches arg to j, and vice versa 
        returns True if this changes anything
        """
        changed = False
        for config in self.configs:
            if config[0]==4: # action is "Open View"
                if config[1]==i:
                    config[1]=j
                    changed = True
                elif config[1]==j:
                    config[1]=i
                    changed = True
        return changed
    
    def shift_views(self, start, up=True):
        """
        if any button's action is to Open View i, where i>=start, arg is incremented if up else decremented
        returns True if this changes anything
        """
        changed = False
        delta = 1 if up else -1
        for config in self.configs:
            if config[0]==4: # action is "Open View"
                if config[1]>=start:
                    config[1]=config[1]+delta
                    changed = True
        return changed
    
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