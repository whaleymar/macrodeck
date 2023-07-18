import os

try:
    import vlc

    HAS_VLC = True
except ModuleNotFoundError:
    HAS_VLC = False


# class that maintains VLC Players and tracks their states
# if i was smart this would inherit from vlc.instance
class VLCPlayer:
    def __init__(self):
        self.vlc_instance = vlc.Instance()
        self.players = []
        self.nplayers = 0
        self.playlist_mode = False
        self.playlist_paused = False
        self.volume = 50

    def __call__(self, path, new=False):
        if new or not self.nplayers:
            player = self.new_player()
            player.audio_set_volume(self.volume)
            self.players.append(player)
            self.nplayers += 1
        else:
            player = self.players[0]

        player.set_media(self.vlc_instance.media_new(path))
        print(f"Playing {os.path.basename(path)}".encode("utf8"))
        player.play()

    def new_player(self):
        return self.vlc_instance.media_player_new()

    def stop(self):
        for player in self.players:
            player.stop()

    def reset(self):
        self.stop()
        self.players = []
        self.nplayers = 0
        self.playlist_mode = False
        self.playlist_paused = False

    def playing(self, player=None):
        # checks if the given player is playing,
        # if none given, checks the default player

        if self.nplayers == 0:
            return False
        elif player is None:
            player = self.default_player()
        return player.get_state() == vlc.State.Playing

    def default_player(self):
        # returns the default player if it exists, else None
        if not self.nplayers:
            return None
        return self.players[0]

    def toggle_pause(self):
        # works only for default player

        if not self.nplayers:
            return

        player = self.default_player()
        if self.playing(player):
            player.pause()
            if self.playlist_mode:
                self.playlist_paused = True
        else:
            player.play()
            if self.playlist_mode:
                self.playlist_paused = False

    def set_volume(self, value):
        # works only for default player
        self.volume = value

        if not self.nplayers:
            return

        player = self.default_player()
        player.audio_set_volume(value)
