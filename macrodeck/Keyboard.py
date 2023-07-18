import time

from pynput._util import win32_vks  # gets keycodes
from pynput.keyboard import (  # threading/thread wrapper for hotkeys
    Controller,
    HotKey,
    KeyCode,
    Listener,
)


# Create custom pynput class to avoid a bug with virtual key codes: ########
class MyHotKey(HotKey):
    def press(self, key):
        # remove scan code from input key because it's not input correctly in the hotkey
        if hasattr(key, "_scan"):
            setattr(key, "_scan", None)
        if key in self._keys and key not in self._state:
            self._state.add(key)
            if self._state == self._keys:
                self._on_activate()

    def release(self, key):
        """Updates the hotkey state for a released key.

        :param key: The key being released.
        :type key: Key or KeyCode
        """
        # remove scan code from input key because it's not input correctly in the hotkey
        if hasattr(key, "_scan"):
            setattr(key, "_scan", None)
        if key in self._state:
            self._state.remove(key)

        # TODO try just clearing self._state here to avoid sticky hotkeys


class MyGlobalHotKeys(Listener):
    """A keyboard listener supporting a number of global hotkeys.

    This is a convenience wrapper to simplify registering a number of global
    hotkeys.

    :param dict hotkeys: A mapping from hotkey description to hotkey action.
        Keys are strings passed to :meth:`HotKey.parse`.

    :raises ValueError: if any hotkey description is invalid
    """

    def __init__(self, hotkeys, *args, **kwargs):
        self._hotkeys = [
            MyHotKey(HotKey.parse(key), value) for key, value in hotkeys.items()
        ]
        super(MyGlobalHotKeys, self).__init__(
            on_press=self._on_press, on_release=self._on_release, *args, **kwargs
        )

    def _on_press(self, key):
        """The press callback.

        This is automatically registered upon creation.

        :param key: The key provided by the base class.
        """
        for hotkey in self._hotkeys:
            hotkey.press(self.canonical(key))

    def _on_release(self, key):
        """The release callback.

        This is automatically registered upon creation.

        :param key: The key provided by the base class.
        """
        for hotkey in self._hotkeys:
            hotkey.release(self.canonical(key))


##############################
# Macro Keyboard Class: ###########
##############################


class keyboard(Controller):
    def press_keys(self, keys, seconds=0.0):
        for key in keys:
            self.press(key)
        if seconds:
            time.sleep(seconds)
        for key in keys:
            self.release(key)

        time.sleep(
            0.1
        )  # need some delay between each key press to prevent bugs. Not sure what the minimum is
        return


##############################
# HotKey Functions: ###########
##############################


def init_hotkeys(buttons):
    hkmap = hotkeymap(buttons)
    return MyGlobalHotKeys(hkmap)


def hotkeymap(buttons):
    hotkeys = [(button.modifier, button.key, button.run_action) for button in buttons]
    return {
        f"{hotkey[0]}<{keycode(hotkey[1][1:-1])}>"
        if hotkey[1][0] == "<" and hotkey[1][-1] == ">"
        else f"{hotkey[0]}{hotkey[1]}": hotkey[2]
        for hotkey in hotkeys
    }


#######################################################
# Helper Functions (for threads and hotkeys): ##########
#######################################################


def keycode(key):
    if key[0] == "<" and key[-1] == ">":
        key = key[1:-1]
    return eval(f"win32_vks.{key.upper()}")


def to_pynput(key):
    return key if len(key) == 1 else KeyCode.from_vk(keycode(key))
