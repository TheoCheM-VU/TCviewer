import os
import yaml
from typing import Any


STYLE_DIRECTORY = os.path.join(os.path.dirname(__file__), 'styles')
ATOM_COLORS_DIRECTORY = os.path.join(os.path.dirname(__file__), 'atom_colors')
ATOM_RADII_DIRECTORY = os.path.join(os.path.dirname(__file__), 'atom_radii')


def get_styles():
	return [file.removesuffix('.yaml') for file in os.listdir(STYLE_DIRECTORY) if file.endswith('.yaml')]


def get_atom_color_conventions():
	return [file.removesuffix('.yaml') for file in os.listdir(ATOM_COLORS_DIRECTORY) if file.endswith('.yaml')]

def get_atom_colors(convention):
	with open(os.path.join(ATOM_COLORS_DIRECTORY, f'{convention}.yaml')) as params:
		colors = yaml.safe_load(params.read())
	return colors

def get_atom_color(symbol, convention):
	return get_atom_colors(convention).get(symbol, get_atom_colors(convention)['default'])


def get_atom_radius_conventions():
	return [file.removesuffix('.yaml') for file in os.listdir(ATOM_RADII_DIRECTORY) if file.endswith('.yaml')]

def get_atom_radii(convention):
	with open(os.path.join(ATOM_RADII_DIRECTORY, f'{convention}.yaml')) as params:
		radii = yaml.safe_load(params.read())
	return radii

def get_atom_radius(symbol, convention):
	return get_atom_radii(convention).get(symbol)



class rcParamsLoader(dict):
	def __init__(self, path: str = None):
		super().__init__()
		if path is not None:
			self.load(path)

	def load(self, path: str):
		with open(path) as params:
			self.__dict__.update(yaml.safe_load(params.read()))

	def __getitem__(self, key: str):
		keys = key.split('.')
		d = self.__dict__
		for k in keys:
			d = d[k]
		return d

	def get_argument(self, key: str, argument: Any) -> Any:
		if argument is None:
			return self[key]
		else:
			return argument


rcParams = rcParamsLoader(os.path.join(STYLE_DIRECTORY, 'default.yaml'))
print(rcParams['atom.scale'])
