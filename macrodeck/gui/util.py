import customtkinter as ctk
from PIL import Image
from screeninfo import get_monitors

def to_rgb(hexstring):
    return tuple(int(hexstring[i:i+2],16) for i in range(1,6,2))

def hovercolor(hexstring):
    return '#%02x%02x%02x' % tuple(max(col-30,0) for col in to_rgb(hexstring))

def ctkimage(path, size):
    return ctk.CTkImage(Image.open(path), size=size)

def genericSwap(sequence, i, j):
    """
    swaps elements at indices i and j in sequence
    mutates the list
    """

    tmp = sequence[i]
    sequence[i] = sequence[j]
    sequence[j] = tmp

def scaling_factor():
    """
    calculates GUI scaling factor based on primary monitor size
    """

    m = None
    for m in get_monitors():
        if m.is_primary:
            break
    if m is None:
        raise ValueError
    return m.height/1440