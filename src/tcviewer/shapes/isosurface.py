from typing import Tuple, Union
import vtk
import tcmu
from tcviewer import (
    shapes, 
    rcParams,
    FloatSetting, 
    ColorSetting, 
    BooleanSetting,)
import numpy as np
from scm import plams
import tcintegral.grid
from vtk.util.numpy_support import numpy_to_vtk


class IsoSurface(shapes.EditableShape):
    def __init__(
        self, 
        parent, 
        data: Union[str, tcintegral.grid.Grid, vtk.vtkStructuredPointsReader],
        isovalue: float,
        name: str = None,

        color: Tuple[float, float, float] = None,
        outline_radius: float = None,
        outline_enabled: bool = None,
        outline_color: Tuple[float, float, float] = None,
        outline_use_surface_color: bool = None,

        opacity: float = None,
        ambient: float = None,
        diffuse: float = None,
        specular: float = None,
        specular_power: float = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.name = name

        self.parent = parent

        # settings holds all properties related to the bond
        self.settings = {}
        self.settings['isovalue']                   = isovalue
        self.settings['color']                      = rcParams.get_argument('isosurface.color', color)
        self.settings['outline_radius']             = rcParams.get_argument('isosurface.outline_radius', outline_radius)
        self.settings['outline_enabled']            = rcParams.get_argument('isosurface.outline_enabled', outline_enabled)
        self.settings['outline_color']              = rcParams.get_argument('isosurface.outline_color', outline_color)
        self.settings['outline_use_surface_color']  = rcParams.get_argument('isosurface.outline_use_surface_color', outline_use_surface_color)

        self.settings['opacity']                    = rcParams.get_argument('isosurface.opacity', opacity)
        self.settings['ambient']                    = rcParams.get_argument('isosurface.ambient', ambient)
        self.settings['diffuse']                    = rcParams.get_argument('isosurface.diffuse', diffuse)
        self.settings['specular']                   = rcParams.get_argument('isosurface.specular', specular)
        self.settings['specular_power']             = rcParams.get_argument('isosurface.specular_power', specular_power)

        self.mcubes = vtk.vtkMarchingCubes()
        if isinstance(data, str):
            try:
                data = tcintegral.grid.from_vtk_file(data)
            except:
                data = tcintegral.grid.from_cube_file(data)

        if isinstance(data, tcintegral.grid.Grid):
            depthArray = numpy_to_vtk(data.values.reshape(*data.shape).ravel(order='F'), deep=True, array_type=vtk.VTK_DOUBLE)
            imdata = vtk.vtkImageData()
            imdata.SetDimensions(data.shape)
            imdata.SetSpacing(data.spacing)
            imdata.SetOrigin(data.origin)
            imdata.GetPointData().SetScalars(depthArray)
            self.mcubes.SetInputData(imdata)
            scale = 1

        elif isinstance(data, vtk.vtkStructuredPointsReader):
            self.mcubes.SetInputConnection(data.GetOutputPort())
            scale = 0.529177249

        self.mcubes.ComputeNormalsOn()
        self.mcubes.ComputeGradientsOn()
        self.mcubes.SetValue(0, isovalue)
        self.mcubes.Update()
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(self.mcubes.GetOutputPort())
        mapper.ScalarVisibilityOff()

        self.surface_actor = vtk.vtkActor()
        self.surface_actor.SetMapper(mapper)
        self.surface_actor.GetProperty().SetColor(self.settings['color'])
        self.surface_actor._original_color = self.settings['color']
        silhouette = vtk.vtkPolyDataSilhouette(input_data=self.mcubes.GetOutput(), camera=self.parent.renderer.active_camera)
        mapper2 = vtk.vtkPolyDataMapper()
        # mapper2.SetNumberOfPieces(100)
        silhouette >> mapper2

        self.silhouette_actor = vtk.vtkActor(mapper=mapper2)
        self.silhouette_actor.property.interpolation = 0
        self.silhouette_actor.property.color = self.settings['color']   
        self.silhouette_actor.property.color = (0, 0, 0)
        self.silhouette_actor.property.line_width = self.settings['outline_radius']

        self.surface_actor.SetScale(scale)
        # self.surface_actor.PickableOff()
        # if isovalue < 0:
        #     self.surface_actor.type = f'surfacem_{gid}'
        # else:
        #     self.surface_actor.type = f'surfacep_{gid}'
        # self.surface_actor.SetUserTransform()

        parent.renderer.AddActor(self.surface_actor)
        parent.renderer.AddActor(self.silhouette_actor)

        self._reset_properties()

        # this actor is used for drawing an outline around the atom
        outlineMapper = vtk.vtkPolyDataMapper()
        outlineMapper.SetInputConnection(self.mcubes.GetOutputPort())

        self.outline_actor = vtk.vtkActor()
        self.outline_actor.SetMapper(outlineMapper)
        self.outline_actor.GetProperty().LightingOff()
        self.outline_actor.GetProperty().SetColor(vtk.vtkNamedColors().GetColor3d('Magenta'))
        # self.outline_actor.SetPosition(self.coords)

    def __str__(self):
        return self.name if self.name is not None else repr(self)

    @FloatSetting('Geometry', 'Outline Radius', 'outline_radius', limits=(0, float('inf')))
    def set_outline_radius(self, outline_radius: float = None):
        self.settings['outline_radius'] = rcParams.get_argument('isosurface.outline_radius', outline_radius)
        self._reset_properties()

    @BooleanSetting('Geometry', 'Draw Outline', 'outline_enabled')
    def set_outline_radius(self, enabled: bool = None):
        self.settings['outline_enabled'] = rcParams.get_argument('isosurface.outline_enabled', enabled)
        self._reset_properties()

    @FloatSetting('Material', 'Opacity', 'opacity', limits=(0, 1))
    def set_opacity(self, opacity: float = None):
        self.settings['opacity'] = rcParams.get_argument('isosurface.opacity', opacity)
        self._reset_properties()

    @FloatSetting('Material', 'Ambient', 'ambient', limits=(0, 1))
    def set_ambient(self, ambient: float = None):
        self.settings['ambient'] = rcParams.get_argument('isosurface.ambient', ambient)
        self._reset_properties()

    @FloatSetting('Material', 'Diffuse', 'diffuse', limits=(0, 1))
    def set_diffuse(self, diffuse: float = None):
        self.settings['diffuse'] = rcParams.get_argument('isosurface.diffuse', diffuse)
        self._reset_properties()

    @FloatSetting('Material', 'Specular', 'specular', limits=(0, 1))
    def set_specular(self, specular: float = None):
        self.settings['specular'] = rcParams.get_argument('isosurface.specular', specular)
        self._reset_properties()

    @FloatSetting('Material', 'Specular Power', 'specular_power', limits=(0, float('inf')))
    def set_specular_power(self, specular_power: float = None):
        self.settings['specular_power'] = rcParams.get_argument('isosurface.specular_power', specular_power)
        self._reset_properties()

    @ColorSetting('Material', 'Color', 'color')
    def set_color(self, color: Tuple[float, float, float] = None):
        self.settings['color'] = rcParams.get_argument('isosurface.color', color)
        self._reset_properties()

    def _reset_properties(self):
        self.silhouette_actor.SetVisibility(self.settings['outline_enabled'])
        self.silhouette_actor.property.line_width = self.settings['outline_radius']

        self.surface_actor.GetProperty().SetOpacity(self.settings['opacity'])
        self.surface_actor.GetProperty().SetAmbient(self.settings['ambient'])
        self.surface_actor.GetProperty().SetDiffuse(self.settings['diffuse'])
        self.surface_actor.GetProperty().SetSpecular(self.settings['specular'])
        self.surface_actor.GetProperty().SetSpecularPower(self.settings['specular_power'])
        self._reset_color()

    def _reset_color(self):
        self.surface_actor.GetProperty().SetColor([x/255 for x in self.settings['color']])
        if self.settings['outline_use_surface_color']:
            self.silhouette_actor.GetProperty().SetColor([x/255 for x in self.settings['color']])
        else:
            self.silhouette_actor.GetProperty().SetColor([x/255 for x in self.settings['outline_color']])
