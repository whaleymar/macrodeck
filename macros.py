from pynput.keyboard import GlobalHotKeys, Key, Controller, KeyCode # threading/thread wrapper for hotkeys
from pynput._util import win32_vks # getting keycodes
import time
import threading # playlist worker thread
from multiprocessing import Queue # communication btwn threads
from util import VLCPlayer, index_library
import os
# import keycodes

##############################
# Hot Key Functions: #########
##############################
def playsong(path):
	player(path)

def playrsong():
	player(lib.rsong())

def shuffle():
	q_clear()
	for song in lib.shuffle('ACTION'):
		plq.put(song)
		print(os.path.basename(song)) # for debug
	print('\n')
	player.playlist_mode = True

def skipsong():
	# skips song in playlist
	player.stop()

def stopsongs():
	q_clear()
	player.reset()

def pause():
	player.toggle_pause()

def terminate():
	# clear queue and shut down
	q_clear()
	hotkeys.stop()

def printstatus():
	print("Playing: ", player.playing())
	print(f"There are {len(player.players)} player(s)")
	print(f"Playlist mode: {player.playlist_mode}\nPlaylist paused: {player.playlist_paused}")
	print(lib.lib)

##############################
# HotKeys: ###########
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

def playlist_worker():
	while True:
		if not player.playing() and not player.playlist_paused:
			song = plq.get()
			player(song)
			time.sleep(1) # sleep after playing a song so player's state has time to update; not sure if I can make it shorter
		else:
			time.sleep(1)
			continue

##############################
# Macros: ###########
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

#######################################################
# Helper Functions (for threads and hotkeys): ##########
#######################################################

def q_clear():
	while not plq.empty():
		plq.get()
	time.sleep(0.05) # makes sure another song doesn't accidentally get played

def keycode(key):
	if key[0]=='<' and key[-1]=='>':
		key = key[1:-1]
	return eval(f"win32_vks.{key.upper()}")

def to_pynput(key):
	return key if len(key)==1 else KeyCode.from_vk(keycode(key))

if __name__=='__main__':

	# initialize music library
	parent = r"C:\Users\cwhal\Content\music"
	ignore = ['1. Ignore', '2. SoundEffects', '3. To Edit']
	lib = index_library(parent, ignore=ignore)

	# initialize media player
	player = VLCPlayer()

	# create playlist queue and threads
	plq = Queue() # FIFO

	hotkeys = init_hotkeys() # threading.thread instance
	hotkeys.start()
	pl_thread = threading.Thread(target=playlist_worker, daemon=True, name="playlist")
	pl_thread.start()
	hotkeys.join()