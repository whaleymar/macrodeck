import customtkinter as ctk

import macrodeck.ActionClasses as act
from macrodeck.Actions import ACTIONS, HAS_OBSWS
from macrodeck.gui.style import FC_DEFAULT, FC_DEFAULT2, FC_EMPTY, ICON_SIZE, WRAPLEN
from macrodeck.gui.util import ctkimage, hovercolor

BACK_ICON = ctkimage("assets/action_back.png", size=ICON_SIZE)

# get index of "Open View" Action within ACTIONS
OPENVIEW_IX = None
for action in ACTIONS:
    if isinstance(action, act.OpenView):
        OPENVIEW_IX = action.enum
        break
if OPENVIEW_IX is None:
    raise ValueError("'OpenView' action not found")


# ctk button wrapper that stores callback/args, hotkeys, and some convenience methods for main keys
class ActionButton(ctk.CTkButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.arg = None
        self.default_text = ""  # if button text is empty, fill with default_text
        self.img_ix = None
        self.action_enum = 0
        self._lock = False
        self._global = False
        self.modifier = None
        self.key = None

    def activate(self):
        # only set default color if we're coming from deactivation
        if self.cget("fg_color") == FC_EMPTY:
            if self.grid_info()["row"] % 2 == 0:
                col = FC_DEFAULT
            else:
                col = FC_DEFAULT2
            self.set_colors(col, None, hovercolor(col))

    def deactivate(self):
        self.set_colors(FC_EMPTY, None, hovercolor(FC_EMPTY))
        self.default_text = ""
        self.set_text("")
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
        self.set_action(OPENVIEW_IX)
        self.set_arg(0)  # point to main view
        self.configure(image=BACK_ICON)
        self._draw()
        self.lock()

    # stores action fxn call enum
    def set_action(self, enum):
        if self.locked():
            return
        self.action_enum = enum

        if not ACTIONS[self.action_enum].requires_arg:
            to_update = ACTIONS[self.action_enum].init_hook(self.master.master)
            self.update_state(to_update)

    def get_action(self):
        return self.action_enum

    # stores action fxn call arg
    def set_arg(self, arg):
        if self.locked():
            return
        self.arg = arg

        if ACTIONS[self.action_enum].requires_arg:
            to_update = ACTIONS[self.action_enum].init_hook(
                self.arg, self.master.master
            )
            self.update_state(to_update)

    def get_arg(self):
        return self.arg

    def set_keys(self, modifier, key):
        if modifier == "none" or modifier == "":
            self.modifier = ""
        else:
            self.modifier = modifier + "+"  # add '+' for modifier for convenience
        self.key = key

    def get_keys(self):
        if self.modifier is None and self.key is None:
            return None
        return self.modifier[:-1], self.key  # [:-1] since we add '+' to modifier

    def set_text(self, text, default=False, wraplen=None):
        # set button text
        # if default: sets default text attribute

        if self.locked():
            return

        # sometimes this setting gets overwritten by other ops, so resetting it here for max coverage
        if self._text_label is None:
            self.configure(text=" ")
            self.configure(text="")
            if wraplen is None:
                self._text_label.configure(wraplength=WRAPLEN)
            else:
                self._text_label.configure(wraplength=wraplen)

        if default and self.default_text == self.cget("text"):
            # wipe default text if we are overwriting
            self.configure(text="")

        if default:
            self.default_text = text
        else:
            self.configure(text=text[:35])

        if not self.cget("text") and self.default_text:
            self.configure(text=self.default_text[:35])

    def get_text(self):
        return self.cget("text"), self.default_text

    def set_colors(
        self, fg_color=None, border_color=None, hover_color=None, ignore_lock=False
    ):
        if self.locked() and not ignore_lock:
            return

        if fg_color is not None:
            self.configure(fg_color=fg_color)
        if border_color is not None:
            self.configure(border_color=border_color)
        if hover_color is not None:
            self.configure(hover_color=hover_color)

    def get_colors(self):
        return (
            self.cget("fg_color"),
            self.cget("border_color"),
            self.cget("hover_color"),
        )

    def set_image(self, ix=None, images=None):
        # show given image or default image if not given
        if self.locked():
            return

        self.img_ix = ix

        if ix is None:
            self.configure(image=ACTIONS[self.action_enum].icon)
        else:
            self.configure(image=images[ix])
        self._draw()

    def get_image(self):
        return self.img_ix

    def update_state(self, to_update):
        if to_update is None:
            return

        for key, args in to_update.items():
            if key == "colors":
                self.set_colors(*args, ignore_lock=True)
            elif key == "args":
                self.set_arg(args)
            else:
                print(f"Unhandled key: {key}")

    def run_action(self):
        # check that we have an action and, if needed, an arg

        to_update = None

        if self.action_enum is None or (
            ACTIONS[self.action_enum].requires_arg and self.arg is None
        ):
            self.master.master.helpertxt_noconfig()
            return

        if ACTIONS[self.action_enum].requires_arg:
            to_update = ACTIONS[self.action_enum](
                self.arg, self.master.master
            )  # self.master.master is fragile if I add more frames. Should use direct pointer to main window TODO (am using in multiple places in class)
        else:
            to_update = ACTIONS[self.action_enum](self.master.master)

        self.update_state(to_update)

    def dump(self):
        """
        returns (mutable) button metadata (used for saving)

        self.get_action() should always be first,
        and self.get_arg() second
        """

        return [
            self.get_action(),
            self.get_arg(),
            self.get_keys(),
            self.get_text(),
            self.get_colors(),
            self.get_image(),
        ]

    # override this to stop buttons from resizing
    def _create_grid(self):
        # messing with weighting so action icon doesn't move with text
        if self._text_label is not None:
            self._text_label.grid_propagate(0)

        if self._compound == "right":
            if self._image_label is not None:
                self._image_label.grid(row=2, column=3, sticky="w")
            if self._text_label is not None:
                self._text_label.grid(row=2, column=1, sticky="e")
        elif self._compound == "left":
            if self._image_label is not None:
                self.grid_columnconfigure(1, weight=1)
            if self._text_label is not None:
                self.grid_columnconfigure(2, weight=1)

            if self._image_label is not None:
                self._image_label.grid(row=1, column=1, padx=5, sticky="w")
            if self._text_label is not None:
                self._text_label.grid(row=1, column=2, padx=5, sticky="w")
        elif self._compound == "top":
            if self._image_label is not None:
                self._image_label.grid(row=1, column=2, sticky="s")
            if self._text_label is not None:
                self._text_label.grid(row=3, column=2, sticky="n")

        elif self._compound == "bottom":
            if self._image_label is not None:
                self.grid_rowconfigure(3, weight=1)

            # TODO if no text label then put image at top (and make big)
            if self._image_label is not None:
                self._image_label.grid(row=3, column=2, pady=3, sticky="s")
            if self._text_label is not None:
                self._text_label.grid(row=0, column=2, pady=2, sticky="n")
