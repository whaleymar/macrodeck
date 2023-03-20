from pynput.keyboard import GlobalHotKeys # threading/thread wrapper for hotkeys
from pynput._util import win32_vks # getting keycodes
import time
import threading # playlist worker thread
from multiprocessing import Queue # communication btwn threads
from util import VLCPlayer, index_library
import os

##############################
# Hot Key Functions: #########
##############################
def playsong():
	player(lib.rsong())

def shuffle():
	q_clear()
	for song in lib.shuffle('PUMP UP'):
		plq.put(song)
		print(os.path.basename(song)) # for debug
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
	macros.stop()

def printstatus():
	print("Playing: ", player.playing())
	print(f"There are {len(player.players)} player(s)")
	print(f"Playlist mode: {player.playlist_mode}\nPlaylist paused: {player.playlist_paused}")
	print(lib.lib)

##############################
# Threading Stuff: ###########
##############################

def init_macros():
	return GlobalHotKeys({
		f'<ctrl>+<shift>+<{keycode("F1")}>': terminate,
		f'<{keycode("PAUSE")}>': pause,
		f'<ctrl>+<{keycode("F3")}>': skipsong,
		f'<ctrl>+<{keycode("F1")}>': stopsongs,
		f'<ctrl>+<{keycode("F2")}>': playsong,
		f'<ctrl>+<shift>+<{keycode("F3")}>': shuffle,
		f'<ctrl>+<{keycode("F12")}>': printstatus
		})

def playlist_worker():
	while True:
		if not player.playing() and not player.playlist_paused:
			song = plq.get()
			player(song)
			time.sleep(1) # sleep after playing a song so player's state has time to update; not sure if I can make it shorter
		else:
			time.sleep(1)
			continue

#######################################################
# Helper Functions (for threads and macros): ##########
#######################################################

def q_clear():
	while not plq.empty():
		plq.get()
	time.sleep(0.05) # makes sure another song doesn't accidentally get played

def keycode(key):
	return eval(f"win32_vks.{key.upper()}")

if __name__=='__main__':

	# initialize music library
	parent = r"C:\Users\cwhal\Content\music"
	ignore = ['1. Ignore', '2. SoundEffects', '3. To Edit']
	lib = index_library(parent, ignore=ignore)

	# initialize media player
	player = VLCPlayer()

	# create playlist queue and threads
	plq = Queue() # FIFO

	macros = init_macros() # threading.thread instance
	macros.start()
	pl_thread = threading.Thread(target=playlist_worker, daemon=True, name="playlist")
	pl_thread.start()
	macros.join()