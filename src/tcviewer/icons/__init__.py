import os
from PySide6 import QtGui


ICON_FOLDER = os.path.dirname(__file__)

def get_icon(name):
	return QtGui.QIcon(os.path.join(ICON_FOLDER, name + '.png'))
