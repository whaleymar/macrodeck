import customtkinter as ctk
from PIL import Image
from screeninfo import get_monitors


def to_rgb(hexstring):
    return tuple(int(hexstring[i : i + 2], 16) for i in range(1, 6, 2))


def hovercolor(hexstring):
    return "#%02x%02x%02x" % tuple(max(col - 30, 0) for col in to_rgb(hexstring))


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
    return m.height / 1440


class OBSString:
    def __init__(self, string, element_constructor=str):
        self.constructor = element_constructor
        self.set_string(string)

    def set_string(self, string):
        self.string = string
        self.compile()

    def compile(self):
        i = 0
        j = i + 1
        self.starter_elements = []

        while i < len(self.string):
            i = self.string.find("{", i)
            if i == -1:
                break
            j = self.string.find("}", i)
            if j == -1:
                raise ValueError("Malformed String")

            elem = self.string[i : j + 1]
            self.starter_elements.append(elem)
            i = j + 1

        self.elements = []
        for i in range(len(self.starter_elements)):
            elem = self.starter_elements[i]
            self.string = self.string.replace(elem, "{}")
            self.elements.append(self.constructor(elem[1:-1]))

    def format_string(self):
        if len(self.elements) == 0:
            return self.string

        return self.string.format(*self.elements)

    def update_string(self):
        """
        updates internal fstring representation and returns button arg with updated elems
        """
        if len(self.elements) == 0:
            return self.string
        new_fstring = self.string.format(*[f"{{{elem}}}" for elem in self.elements])
        self.set_string(new_fstring)
        return new_fstring
