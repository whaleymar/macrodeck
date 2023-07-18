import time
from functools import partial

import customtkinter as ctk

from macrodeck import ActionClasses
from macrodeck.gui.ActionButton import ActionButton
from macrodeck.gui.style import (
    BC_ACTIVE,
    BC_DEFAULT,
    FC_DEFAULT,
    FC_DEFAULT2,
    FC_EMPTY,
    ICON_SIZE,
    ICON_SIZE_WIDE,
)
from macrodeck.gui.util import ctkimage, hovercolor

XPAD = 3
YPAD = 3
WRAPLEN_MA = 150

# this should be imported by App.py


class MultiAction(ActionClasses.Action):
    def __init__(self):
        super().__init__("Multi Action", None, None, requires_arg=True)  # TODO image
        self.app = None  # store pointer to use some app methods
        self.created_frames = False
        self.secs_between_actions = 0.2

        # UI stuff:
        self.square_dim = 40  # dim of +/x buttons
        self.pad = 4

    def _widget(self, app, frame, changed):
        """
        sets flex button to "config multi action" button
        """

        if self.app is None:
            self.app = app

        button = ctk.CTkButton(
            frame,
            command=partial(self.open_gui, changed),
            text="Edit Actions",
            fg_color=FC_DEFAULT,
            hover_color=hovercolor(FC_DEFAULT),
            font=app.STANDARDFONT,
        )

        return button, None

    def __call__(self, arg, app):
        """
        runs each action in loop
        """
        if self.app is None:
            self.app = app
        app.after(100, self.run_actions, arg)

    def unique_key(self) -> int:
        return 11

    def run_actions(self, arg):
        actions = self.app.get_actions()
        for config in arg:
            action_enum = config[0]
            action_arg = config[1]
            if action_enum is None or (
                actions[action_enum].requires_arg and action_arg is None
            ):
                continue
            if actions[action_enum].calls_after:
                if actions[action_enum].requires_arg:
                    actions[action_enum](action_arg, self.app, multi_action=True)
                else:
                    actions[action_enum](self.app, multi_action=True)
            else:
                if actions[action_enum].requires_arg:
                    actions[action_enum](action_arg, self.app)
                else:
                    actions[action_enum](self.app)

            time.sleep(self.secs_between_actions)

    def button_callback(self, button_ix):
        """
        runs when we click a button w/ the mouse
        """

        # reset dynamic vars
        # app.reset_bordercols()
        if (
            self.app.current_button is not None
            and self.app.current_button in self._actions
        ):  # don't do anything if button was deleted
            self.app.current_button.configure(border_color=BC_DEFAULT)

        self.app.helpertxt_clear()
        self.app.current_button = self._actions[button_ix]

        # highlight selected button
        self._actions[button_ix].configure(border_color=BC_ACTIVE)

        # set current button details in editor:
        self.app.button_callback_MA()

    def open_gui(self, changed):
        """
        Opens frame for multi action config
        """

        self.app.helpertxt_clear()
        if self.app.current_button is None:
            self.app.helpertxt_nobtn()
            return

        if not self.created_frames:
            self.init_frames(self.app.STANDARDFONT)

        self.init_rows(changed, None if changed else self.app.current_button.get_arg())

        self.app.showActionMenu()

    def init_frames(self, font):
        # resize MAframe to match topframe's dimensions, then lock dims and add weights
        self.width = self.app.topframe.winfo_width()
        self.height = self.app.topframe.winfo_height()
        self.app.MAframe.configure(width=self.width, height=self.height)
        self.app.MAframe.grid_propagate(0)
        self.app.MAframe.grid_columnconfigure(0, weight=1)
        self.app.MAframe.grid_rowconfigure(0, weight=1)

        # scrollable frame for action buttons
        self.sframe = ctk.CTkScrollableFrame(
            master=self.app.MAframe, width=self.width, height=self.height
        )
        self.sframe.grid_columnconfigure(0, weight=1)
        self.sframe.grid_columnconfigure(1, weight=1)
        self.sframe.grid_rowconfigure(0, weight=1)
        self.sframe.grid(row=0, column=0, columnspan=2, sticky="", padx=XPAD, pady=YPAD)

        self.font = font

        self.okbutton = ctk.CTkButton(
            master=self.app.MAframe,
            text="OK",
            command=self._ok_event,
            font=font,
            fg_color=FC_DEFAULT,
            hover_color=hovercolor(FC_DEFAULT),
        )
        self.okbutton.grid(row=2, column=0, sticky="", padx=XPAD, pady=YPAD)

        self.cancelbutton = ctk.CTkButton(
            master=self.app.MAframe,
            text="Cancel",
            command=self._cancel_event,
            font=font,
            fg_color=BC_DEFAULT,
            hover_color=hovercolor(BC_DEFAULT),
        )
        self.cancelbutton.grid(row=2, column=1, sticky="", padx=XPAD, pady=YPAD)

    def init_rows(self, changed, args):
        """
        in self.sframe, each row will be an ActionButton instance, and we'll use app.current_button to
        track which one we're editing
        this means we can use all app methods which mutate current button
        """

        self.row = 0
        self._actions = []
        self._deletebuttons = []
        self._newbuttons = []

        # topmost new button (nothing else goes in this row)
        self._newtopbutton = ctk.CTkButton(
            master=self.sframe,
            width=self.square_dim,
            height=self.square_dim,
            text="+",
            fg_color=FC_DEFAULT2,
            hover_color=hovercolor(FC_DEFAULT2),
            corner_radius=4,
            font=self.font,
            command=partial(self.new_row, 0),
        )
        self._newtopbutton.grid(row=0, column=2, padx=XPAD, pady=YPAD, sticky="nse")

        # add rows
        if changed or args is None:
            self.new_row(0)
        else:
            for i in range(len(args)):
                self.new_row(i, args[i])

    def new_row(self, ix, config=None):
        # store new action button:
        self._actions.insert(
            ix,
            ActionButton(
                master=self.sframe,
                corner_radius=4,
                width=self.width - self.square_dim * 2 - self.pad * 2,
                height=self.square_dim,
                fg_color="#1e1e1e",
                hover_color=hovercolor("#1e1e1e"),
                #  border_spacing=self.pad,
                text="asdf",
                anchor="w",
                border_width=1,
                border_color=BC_DEFAULT,
                font=self.font,
                compound="left",
                command=partial(self.button_callback, ix),
            ),
        )

        self._actions[ix]._text_label.configure(wraplength=WRAPLEN_MA)

        # undo dummy value
        self._actions[ix].configure(text="")

        if config is not None:
            # set button using args
            self.to_button(self._actions[ix], config)

        # new delete button:
        self._deletebuttons.append(
            ctk.CTkButton(
                master=self.sframe,
                width=self.square_dim,
                height=self.square_dim,
                text="x",
                fg_color="#ff372a",
                hover_color=hovercolor("#ff372a"),
                corner_radius=4,
                font=self.font,
                command=partial(self.delete_row, self.row),
            )
        )

        # new new button
        self._newbuttons.append(
            ctk.CTkButton(
                master=self.sframe,
                width=self.square_dim,
                height=self.square_dim,
                text="+",
                fg_color=FC_DEFAULT2,
                hover_color=hovercolor(FC_DEFAULT2),
                corner_radius=4,
                font=self.font,
                command=partial(self.new_row, self.row + 1),
            )
        )

        # place new/delete buttons on last row
        self._deletebuttons[self.row].grid(
            row=self.row + 1, column=3, padx=XPAD, pady=YPAD, sticky="nse"
        )
        self._newbuttons[self.row].grid(
            row=self.row + 1, column=2, padx=XPAD, pady=YPAD, sticky="nse"
        )

        self.row += 1

        # move buttons down
        for i in range(ix, len(self._actions)):
            self._actions[i].grid(
                row=i + 1, column=0, padx=XPAD, pady=YPAD, sticky="nsw"
            )
            self._actions[i].configure(command=partial(self.button_callback, i))

        # open menu for newly created button
        # self.button_callback(ix)

    def delete_row(self, ix):
        self._actions[ix].destroy()
        self._actions.pop(ix)

        # remove last delete button
        self._deletebuttons[-1].destroy()
        self._deletebuttons.pop()

        # remove last new button
        self._newbuttons[-1].destroy()
        self._newbuttons.pop()

        self.row -= 1

        if len(self._actions) == ix:
            return

        # move lower buttons up
        for i in range(ix, len(self._actions)):
            self._actions[i].grid(
                row=i + 1, column=0, padx=XPAD, pady=YPAD, sticky="nsew"
            )
            self._actions[i].configure(command=partial(self.button_callback, i))

    def get_args(self):
        result = []
        for i in range(len(self._actions)):
            result.append(self._actions[i].dump())

        return result

    def to_button(self, button, config):
        button.default_text = config[3][1]  # have to do this before set_text
        button.set_action(config[0])
        button.set_arg(config[1])

        # get image
        if config[5] is None:
            image = self.app.get_actions()[config[0]].icon
        else:
            image = self.app.images[config[5]]
        button.img_ix = config[5]

        # all methods that call button.configure should go in here
        button.configure(
            text=config[3][0][:35],
            fg_color=config[4][0],
            border_color=config[4][1],
            hover_color=config[4][2],
            image=image,
        )

        if button._text_label is None:
            button.configure(text=" ")
            button.configure(text="")
        button._text_label.configure(wraplength=WRAPLEN_MA)

    def _ok_event(self):
        # clear border color of cur button
        if (
            self.app.current_button is not None
            and self.app.current_button in self._actions
        ):  # don't do anything if button was deleted
            self.app.current_button.configure(border_color=BC_DEFAULT)

        self.app.showButtons()
        self.app.current_button.set_arg(
            self.get_args()
        )  # set current button to list of actions
        self.close()

    def _cancel_event(self):
        self.app.showButtons()
        self.close()

    def close(self):
        # reset rows
        for i in range(len(self._actions)):
            self._actions[i].destroy()
            self._newbuttons[i].destroy()
            self._deletebuttons[i].destroy()
        self._actions = []
        self._newbuttons = []
        self._deletebuttons = []
