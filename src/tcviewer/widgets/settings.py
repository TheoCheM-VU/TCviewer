from typing import Any, Tuple, List, get_type_hints, Callable, get_args, Union, Iterable
import inspect
from math import floor, log10
import tcviewer

try:
    from PySide6 import QtWidgets, QtCore, QtGui
    has_qt = True
except ImportError:
    has_qt = False

settings = {
    'atom': {
        'size': 1/2.4,
        'draw_quadrants': True,
        'draw_outline': True,
        'quadrant_follow_camera': True,
        'quadrant_width': 0.02,
    },
    'bond': {
        'radius': 0.08,
        'color': [0, 0, 0],
        'dashed_bond_ratio': .5,
    },
}

if has_qt:
    class SettingsTab(QtWidgets.QWidget):
        def __init__(self):
            super().__init__()
            self.layout = QtWidgets.QGridLayout()
            self.setLayout(self.layout)
            self.widget_value_getters = {}
            self.widgets = {}

        def __enter__(self):
            return self

        def __exit__(self, *args):
            self.layout.setRowStretch(self.layout.rowCount(), 1)

        def add(self, name: str = None, default: Any = None, range: Tuple[float] = None, options: List[str] = None):
            row = self.layout.rowCount()
            self.layout.addWidget(QtWidgets.QLabel('    ' + name + ':'), row, 0)

        def add_checkbox(self, name: str = None, default: bool = True):
            row = self.layout.rowCount()
            self.layout.addWidget(QtWidgets.QLabel('    ' + name + ':'), row, 0)
            widg = QtWidgets.QCheckBox()
            widg.setCheckState(QtCore.Qt.CheckState.Checked if default else QtCore.Qt.CheckState.Unchecked)
            self.layout.addWidget(widg, row, 1)
            self.widgets[name] = widg
            self.widget_value_getters[name] = widg.isChecked

        def add_spinbox(self, name: str = None, default: float = None, minimum: float = None, maximum: float = None, step: float = None, decimals: int = 2, suffix_text: str = None):
            row = self.layout.rowCount()
            self.layout.addWidget(QtWidgets.QLabel('    ' + name + ':'), row, 0)
            widg = QtWidgets.QDoubleSpinBox()
            if default:
                widg.setValue(default)
            if minimum:
                widg.setMinimum(minimum)
            if maximum:
                widg.setMaximum(maximum)
            if decimals:
                widg.setDecimals(decimals)
                if step is None:
                    step = 10**-decimals
            if step:
                widg.setSingleStep(step)

            self.layout.addWidget(widg, row, 1)

            if suffix_text:
                self.layout.addWidget(QtWidgets.QLabel(suffix_text), row, 2)

            self.widgets[name] = widg
            self.widget_value_getters[name] = widg.value

        def add_color(self, name: str = None, default: tuple[float] = None):
            row = self.layout.rowCount()
            self.layout.addWidget(QtWidgets.QLabel('    ' + name + ':'), row, 0)
            sublayout = QtWidgets.QGridLayout()
            self.layout.addLayout(sublayout, row, 1)
            widgR = QtWidgets.QSpinBox()
            widgG = QtWidgets.QSpinBox()
            widgB = QtWidgets.QSpinBox()
            if default:
                widgR.setValue(default[0])
                widgG.setValue(default[1])
                widgB.setValue(default[2])

            widgR.setMinimum(0)
            widgG.setMinimum(0)
            widgB.setMinimum(0)
            widgR.setMaximum(255)
            widgG.setMaximum(255)
            widgB.setMaximum(255)

            sublayout.addWidget(QtWidgets.QLabel('R:'), 0, 1)
            sublayout.addWidget(widgR, 0, 2)
            sublayout.addWidget(QtWidgets.QLabel('G:'), 0, 3)
            sublayout.addWidget(widgG, 0, 4)
            sublayout.addWidget(QtWidgets.QLabel('B:'), 0, 5)
            sublayout.addWidget(widgB, 0, 6)

            class widg:
                def value(self):
                    return (widgR.value()/255, widgG.value()/255, widgB.value()/255)

                def connect(self, func):
                    widgR.valueChanged.connect(func)
                    widgG.valueChanged.connect(func)
                    widgB.valueChanged.connect(func)

            self.widgets[name] = widg()
            self.widget_value_getters[name] = self.widgets[name].value

        def add_slider(self, name: str = None, default: float = None, minimum: float = None, maximum: float = None, step: float = None, decimals: int = 2, suffix_text: str = None):
            row = self.layout.rowCount()
            self.layout.addWidget(QtWidgets.QLabel('    ' + name + ':'), row, 0)
            widg = QtWidgets.QDoubleSpinBox()

            if minimum:
                widg.setMinimum(minimum)
            if maximum:
                widg.setMaximum(maximum)
            if default:
                widg.setValue(default)
            if step:
                widg.setSingleStep(step)
            if decimals:
                widg.setDecimals(decimals)

            self.layout.addWidget(widg, row, 1)

            if suffix_text:
                self.layout.addWidget(QtWidgets.QLabel(suffix_text), row, 2)

            self.widgets[name] = widg
            self.widget_value_getters[name] = widg

        def get_value(self, name: str):
            return self.widget_value_getters[name]()

        def connect(self, func: callable):
            for widg in self.widgets.values():
                if hasattr(widg, 'valueChanged'):
                    widg.valueChanged.connect(func)
                elif hasattr(widg, 'stateChanged'):
                    widg.stateChanged.connect(func)
                else:
                    widg.connect(func)


    class SettingsWidget(QtWidgets.QTabWidget):
        def __init__(self):
            super().__init__()
            self.tabs = {}

        def add_tab(self, tab_name: str):
            widg = SettingsTab()
            self.addTab(widg, tab_name)
            self.tabs[tab_name] = widg
            return widg

        def get_value(self, section: str, name: str):
            return self.tabs[section].get_value(name)


    class DefaultSettings(SettingsWidget):
        def __init__(self):
            super().__init__()

            with self.add_tab('Atom') as tab:
                tab.add_spinbox('Size Ratio', 1/2.4, minimum=0, step=0.05, decimals=3)
                tab.add_checkbox('Draw Quadrants', True)
                tab.add_checkbox('Draw Outline', True)
                tab.add_spinbox('Quadrant Width', default=0.02, minimum=0, step=0.001, decimals=3, suffix_text='Å')

            with self.add_tab('Bond') as tab:
                tab.add_spinbox('Radius', 0.08, minimum=0, decimals=3, suffix_text='Å')
                tab.add_color('Color', (0, 0, 0))
                tab.add_spinbox('Dashed Bond Radius', default=0.04, minimum=0, decimals=3, suffix_text='Å')

            with self.add_tab('Iso Surface') as tab:
                tab.add_spinbox('Iso Value', 0.03, minimum=0, maximum=1, decimals=3)
                tab.add_spinbox('Opacity', 0.15, minimum=0, maximum=1, decimals=2, step=.1)
                tab.add_spinbox('Shininess', 0.0, minimum=0, maximum=1, decimals=2, step=.1)
                tab.add_checkbox('Switch Phase Colors', False)
                tab.add_checkbox('Enable Contour', True)
                tab.add_spinbox('Contour Width', 3, minimum=0, decimals=1, step=.1)

import random
_registered_settings = []



class SettingsWidget(QtWidgets.QSplitter):
    def __init__(self):
        super().__init__()
        self.setOrientation(QtCore.Qt.Vertical)
        self.object_list = QtWidgets.QListWidget()
        self.object_list.setSelectionMode(QtWidgets.QListWidget.ExtendedSelection)
        self.object_list.itemSelectionChanged.connect(self.set_tabs)
        self.addWidget(self.object_list)
        self.settings_tabs = QtWidgets.QTabWidget()
        self.addWidget(self.settings_tabs)
        self.objects = {}

    def add_object(self, obj):
        item = QtWidgets.QListWidgetItem(str(obj))
        self.object_list.addItem(item)
        self.objects[str(item)] = obj

    def set_tabs(self):
        selected_objs = self.object_list.selectedItems()

        self.settings_tabs.clear()
        objs = []
        for sel in selected_objs:
            obj = self.objects[str(sel)]
            obj.enable_outline()
            objs.append(obj)

        for obj in self.objects.values():
            if obj in objs:
                continue
            obj.disable_outline()

        classes = set(obj.__class__.__name__ for obj in objs)

        for cls in classes:
            setts = [row for row in _registered_settings if row[0] == cls]

            tabs = {}

            for sett in setts:
                setting_type, tab, variable, internal_variable, func = sett[1], sett[2], sett[3], sett[4], sett[5]

                if tab not in tabs:
                    frame = QtWidgets.QFrame()
                    frame.setLayout(QtWidgets.QVBoxLayout())
                    tabs[tab] = frame

                if setting_type == 'float':
                    widg = FloatWidget(objs, variable, internal_variable, func, sett[6])
                    tabs[tab].layout().addWidget(widg)

                if setting_type == 'boolean':
                    widg = BooleanWidget(objs, variable, internal_variable, func)
                    tabs[tab].layout().addWidget(widg)

                if setting_type == 'category':
                    widg = CategoryWidget(objs, variable, internal_variable, func, sett[6])
                    tabs[tab].layout().addWidget(widg)

                if setting_type == 'color':
                    widg = ColorWidget(objs, variable, internal_variable, func)
                    tabs[tab].layout().addWidget(widg)


        for tab_name, tab_frame in tabs.items():
            self.settings_tabs.addTab(tab_frame, tab_name)
            tab_frame.layout().addStretch()


# class SettingWidget(QtWidgets.QFrame):
#     def __init__(self, objs, name, internal_variable, func, defaults=None):
#         super().__init__()
#         self.setLayout(QtWidgets.QHBoxLayout())
#         self.layout().addWidget(QtWidgets.QLabel(name))

#         self.func = func
#         self.objs = objs

#         self.defaults = defaults

#         annots = func.__annotations__
#         self.number_of_values = len(annots)
#         # internal_values = [ for obj in objs]
#         internal_values = []
#         for obj in objs:
#             v = obj.settings[internal_variable]
#             if not isinstance(v, list) and not isinstance(v, tuple):
#                 v = [v]

#             internal_values.append(v)

#         # check if the internal_values are all the same
#         # if there is more than 1 different value we set
#         # the value to None
#         def all_same(vals):
#             diffs = []
#             for val in vals:
#                 if val not in diffs:
#                     diffs.append(val)
#             return len(diffs) == 1

#         if all_same(internal_values):
#             internal_values = internal_values[0]
#         else:
#             internal_values = [None] * len(internal_values[0])

#         # add the widgets that actually change the values
#         self.value_getters = []
#         self.value_setters = []
#         self.value_resetters = []
#         limits = limits or {}


#         for val, (name, typ) in zip(internal_values, annots.items()):
#             if typ is float:
#                 sb = QtWidgets.QDoubleSpinBox()
#                 if val is not None:
#                     sb.setValue(val)
#                 sb.setSpecialValueText("Auto")
#                 mi, ma = limits.get(name)
#                 if ma == float('inf'):
#                     ma = 1000
#                 if mi == -float('inf'):
#                     mi = -1000
#                 # step = 10**(floor(log10(abs(val))))
#                 step = .1
#                 sb.setSingleStep(step)
#                 sb.setRange(mi-step/1000, ma)
#                 self.layout().addWidget(sb)
#                 self.value_getters.append(sb.value)
#                 self.value_setters.append(sb.setValue)
#                 self.value_resetters.append(lambda: sb.setValue(sb.minimum()))
#                 sb.valueChanged.connect(self.apply_setting)

#             if typ is bool:
#                 sb = QtWidgets.QCheckBox()
#                 if val is not None:
#                     sb.setChecked(val)
#                 self.layout().addWidget(sb)
#                 self.value_getters.append(sb.isChecked)
#                 self.value_setters.append(sb.setChecked)
#                 self.value_resetters.append(sb.setChecked)
#                 sb.stateChanged.connect(self.apply_setting)

#         # add a reset button
#         reset_button = QtWidgets.QPushButton('⟲')
#         self.layout().addWidget(reset_button)
#         reset_button.clicked.connect(self.reset_value)
#         reset_button.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

#     def get_value(self):
#         return [vg() for vg in self.value_getters]

#     def set_value(self, value):
#         if not isinstance(value, (list, tuple)):
#             value = [value]
#         return [vs(v) for v, vs in zip(value, self.value_setters)]

#     def reset_value(self):
#         return [rs() for rs in self.value_resetters]

#     def apply_value_to_one_obj(self, v, obj):
#         self.func(obj, *v)
#         obj.renderer.GetRenderWindow().Render()

#     def apply_setting(self, objs=None):
#         v = self.get_value()
#         renderers = set()
#         for obj in self.objs:
#             self.func(obj, *v)
#             renderers.add(obj.renderer)

#         for renderer in renderers:
#             renderer.GetRenderWindow().Render()


class SettingWidget(QtWidgets.QFrame):
    def __init__(self, objs, variable_name, internal_variable, func, *args):
        super().__init__()
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addWidget(QtWidgets.QLabel(variable_name))

        self.objs = objs
        self.func = func
        self.internal_variable = internal_variable

        reset_button = QtWidgets.QPushButton('⟲')
        self.layout().addWidget(reset_button)
        reset_button.clicked.connect(self.reset_value)
        reset_button.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Minimum)

    def object_values(self):
        return [obj.settings[self.internal_variable] for obj in self.objs]

    def values_are_the_same(self):
        return all(self.object_values()[0] == val for val in self.object_values())

    def reset_value(self):
        for obj in self.objs:
            self.func(obj, None)
        self.update_renderers()

    def apply_value(self):
        for obj in self.objs:
            self.func(obj, self.get_value())
        self.update_renderers()

    def update_renderers(self):
        renderers = set()
        for obj in self.objs:
            renderers.add(obj.parent.renderer)

        for renderer in renderers:
            renderer.GetRenderWindow().Render()



class FloatWidget(SettingWidget):
    def __init__(self, objs, variable_name, internal_variable, func, limits, steps=None):
        super().__init__(objs, variable_name, internal_variable, func)

        # obtain the number of floats that the function expects
        annot = list(func.__annotations__.values())[0]  # the functions should only have one argument
        # by default it is 1
        number_of_floats = 1
        # it may also be given as a typing.Tuple to indicate multiple floats
        if annot is not float:
            number_of_floats = len(get_args(annot))

        self.spin_boxes = []
        # we add the correct amount of spinboxes
        for i in range(number_of_floats):
            sb = QtWidgets.QDoubleSpinBox()
            self.spin_boxes.append(sb)

            sb.setSpecialValueText("Auto")

            if isinstance(limits[0], Iterable):
                mi, ma = limits[i]
            else:
                mi, ma = limits
            if ma == float('inf'):
                ma = 1000
            if mi == -float('inf'):
                mi = -1000

            if steps is None:
                step = 0.1
            else:
                step = steps[i]

            sb.setSingleStep(step)
            sb.setRange(mi-step/1000, ma)

            if self.values_are_the_same() and self.object_values()[0] is not None:
                if isinstance(self.object_values()[0], Iterable):
                    sb.setValue(self.object_values()[0][i])
                else:
                    sb.setValue(self.object_values()[0])

            self.layout().insertWidget(i, sb)
            sb.valueChanged.connect(self.apply_value)


    def get_value(self):
        vals = [sb.value() for sb in self.spin_boxes]
        if len(vals) == 1:
            return vals[0]
        return vals

    def reset_value(self):
        super().reset_value()
        if not self.values_are_the_same():
            [sb.setValue(sb.minimum()) for sb in self.spin_boxes]
        else:
            [sb.setValue(val) for sb, val in zip(self.spin_boxes, self.object_values)]


class BooleanWidget(SettingWidget):
    def __init__(self, objs, variable_name, internal_variable, func):
        super().__init__(objs, variable_name, internal_variable, func)

        self.check_box = QtWidgets.QCheckBox()
        if not self.values_are_the_same():
            self.check_box.setCheckState(QtCore.Qt.PartiallyChecked)
        elif self.object_values()[0]:
            self.check_box.setCheckState(QtCore.Qt.Checked)
        else:
            self.check_box.setCheckState(QtCore.Qt.Unchecked)

        self.layout().insertWidget(0, self.check_box)
        self.check_box.checkStateChanged.connect(self.apply_value)


    def get_value(self):
        return self.check_box.isChecked()

    def reset_value(self):
        super().reset_value()
        if not self.values_are_the_same():
            self.check_box.setCheckState(QtCore.Qt.PartiallyChecked)
        elif self.object_values()[0]:
            self.check_box.setCheckState(QtCore.Qt.Checked)
        else:
            self.check_box.setCheckState(QtCore.Qt.Unchecked)


class CategoryWidget(SettingWidget):
    def __init__(self, objs, variable_name, internal_variable, func, options):
        super().__init__(objs, variable_name, internal_variable, func)

        self.combo_box = QtWidgets.QComboBox()
        self.options = options
        self.set_items()
        self.layout().insertWidget(0, self.combo_box)
        self.combo_box.currentTextChanged.connect(self.apply_value)

    def set_items(self):
        self.combo_box.clear()
        self.combo_box.addItems(self.options())
        if self.values_are_the_same():
            self.combo_box.setCurrentText(self.object_values()[0])


    def get_value(self):
        return self.combo_box.currentText()

    def reset_value(self):
        super().reset_value()
        self.set_items()


class LineEditColorDialogWidget(QtWidgets.QLineEdit):
    def __init__(self, parent=None):
        super(LineEditColorDialogWidget, self).__init__(parent)

        icon = tcviewer.icons.get_icon('rgb')
        action = self.addAction(icon, QtWidgets.QLineEdit.TrailingPosition)
        action.triggered.connect(self.select_color)

    def select_color(self):
        curr_color = QtGui.QColor(self.text())
        new_color = QtWidgets.QColorDialog.getColor(curr_color)
        if not new_color.isValid():
            return
        self.setText(new_color.name())



class ColorWidget(SettingWidget):
    def __init__(self, objs, variable_name, internal_variable, func):
        super().__init__(objs, variable_name, internal_variable, func)

        self.color_line_edit = LineEditColorDialogWidget()
        self.layout().insertWidget(0, self.color_line_edit)
        self.color_line_edit.textChanged.connect(self.apply_value)

        if self.values_are_the_same() and self.object_values()[0] is not None:
            self.color_line_edit.setText(self.rgb_to_hex(self.object_values()[0]))

    def hex_to_rgb(self, hx: str) -> Tuple[int, int, int]:
        R, G, B = int(hx[1:3], 16), int(hx[3:5], 16), int(hx[5:7], 16)
        return R, G, B

    def rgb_to_hex(self, rgb: Tuple[int, int, int]) -> str:
        return f'#{hex(rgb[0])[2:]:02}{hex(rgb[1])[2:]:02}{hex(rgb[2])[2:]:02}'

    def get_value(self):
        text = self.color_line_edit.text()
        return self.hex_to_rgb(text)

    def reset_value(self):
        super().reset_value()



def register_setting(category: str, variable_name: str, internal_name: str, limits: dict = None):
    def inner_dec(func):
        cls = func.__qualname__.split('.')[-2]
        _registered_settings.append((category, variable_name, internal_name, limits, func, cls))
        return func
    return inner_dec


def FloatSetting(category: str, variable_name: str, internal_name: str, limits: Union[Tuple[float, float], List[Tuple[float, float]]] = None, steps: Union[float, List[float]] = None):
    def inner_dec(func):
        cls = func.__qualname__.split('.')[-2]
        _registered_settings.append((cls, 'float', category, variable_name, internal_name, func, limits, steps))
        return func
    return inner_dec


def ColorSetting(category: str, variable_name: str, internal_name: str):
    def inner_dec(func):
        cls = func.__qualname__.split('.')[-2]
        _registered_settings.append((cls, 'color', category, variable_name, internal_name, func))
        return func
    return inner_dec


def CategorySetting(category: str, variable_name: str, internal_name: str, options: Callable = None):
    def inner_dec(func):
        cls = func.__qualname__.split('.')[-2]
        _registered_settings.append((cls, 'category', category, variable_name, internal_name, func, options))
        return func
    return inner_dec


def BooleanSetting(category: str, variable_name: str, internal_name: str):
    def inner_dec(func):
        cls = func.__qualname__.split('.')[-2]
        _registered_settings.append((cls, 'boolean', category, variable_name, internal_name, func))
        return func
    return inner_dec


if __name__ == '__main__':
    sett = SettingsWidget()
    with sett.add_tab('Atom') as tab:
        ...
