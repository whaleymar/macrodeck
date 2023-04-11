from pynput.keyboard import GlobalHotKeys, Controller, KeyCode # threading/thread wrapper for hotkeys
from pynput._util import win32_vks # gets keycodes
import time

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
		
		time.sleep(0.1)
		return

##############################
# HotKey Functions: ###########
##############################

def init_hotkeys(buttons):
	hkmap = hotkeymap(buttons)
	return GlobalHotKeys(hkmap)

def reset_hotkeys(buttons, cur_thread=None):
	if cur_thread is not None:
		cur_thread.stop()

	new_thread = init_hotkeys(buttons)
	new_thread.start()
	return new_thread

def hotkeymap(buttons):
	hotkeys = [(button.modifier, button.key, button.run_action) for button in buttons]
	return {
		f'{hotkey[0]}<{keycode(hotkey[1][1:-1])}>' if hotkey[1][0]=='<' and hotkey[1][-1]=='>' else\
		   f'{hotkey[0]}{hotkey[1]}': hotkey[2]
		for hotkey in hotkeys
		}

#######################################################
# Helper Functions (for threads and hotkeys): ##########
#######################################################

def keycode(key):
	if key[0]=='<' and key[-1]=='>':
		key = key[1:-1]
	return eval(f"win32_vks.{key.upper()}")

def to_pynput(key):
	return key if len(key)==1 else KeyCode.from_vk(keycode(key))