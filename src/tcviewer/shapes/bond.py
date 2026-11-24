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


class Bond(shapes.EditableShape):
    def __init__(
        self, 
        parent, 
        a1: shapes.Atom, 
        a2: shapes.Atom,
        name: str = None,

        radius: float = None,
        color: Tuple[float, float, float] = None,
        outline_radius: float = None,
        outline_enabled: bool = None,
        outline_color: Tuple[float, float, float] = None,
        use_atom_colors: bool = None,

        opacity: float = None,
        ambient: float = None,
        diffuse: float = None,
        specular: float = None,
        specular_power: float = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.a1 = a1
        self.a2 = a2
        self.name = name

        self.parent = parent

        # settings holds all properties related to the bond
        self.settings = {}
        self.settings['radius']             = rcParams.get_argument('bond.radius', radius)
        self.settings['color']              = rcParams.get_argument('bond.color', color)
        self.settings['outline_radius']     = rcParams.get_argument('bond.outline_radius', outline_radius)
        self.settings['outline_enabled']    = rcParams.get_argument('bond.outline_enabled', outline_enabled)
        self.settings['outline_color']      = rcParams.get_argument('bond.outline_color', outline_color)
        self.settings['use_atom_colors']    = rcParams.get_argument('bond.use_atom_colors', use_atom_colors)

        self.settings['opacity']            = rcParams.get_argument('bond.opacity', opacity)
        self.settings['ambient']            = rcParams.get_argument('bond.ambient', ambient)
        self.settings['diffuse']            = rcParams.get_argument('bond.diffuse', diffuse)
        self.settings['specular']           = rcParams.get_argument('bond.specular', specular)
        self.settings['specular_power']     = rcParams.get_argument('bond.specular_power', specular_power)

        c1 = np.array(a1.coords)
        c2 = np.array(a2.coords)

        self.line_source = vtk.vtkLineSource()
        self.line_source.SetPoint1(c1)
        self.line_source.SetPoint2(c2)

        self.line_source1 = vtk.vtkLineSource()
        self.line_source1.SetPoint1(c1)
        self.line_source1.SetPoint2((c1 + c2) / 2)

        self.line_source2 = vtk.vtkLineSource()
        self.line_source2.SetPoint1((c1 + c2) / 2)
        self.line_source2.SetPoint2(c2)

        self.tube_filter = vtk.vtkTubeFilter()
        self.tube_filter.source = self.line_source
        self.tube_filter.SetInputConnection(self.line_source.GetOutputPort())
        self.tube_filter.SetRadius(self.settings['radius'])
        self.tube_filter.SetNumberOfSides(40)

        self.tube_filter1 = vtk.vtkTubeFilter()
        self.tube_filter1.source = self.line_source1
        self.tube_filter1.SetInputConnection(self.line_source1.GetOutputPort())
        self.tube_filter1.SetRadius(self.settings['radius'])
        self.tube_filter1.SetNumberOfSides(20)

        self.tube_filter2 = vtk.vtkTubeFilter()
        self.tube_filter2.source = self.line_source2
        self.tube_filter2.SetInputConnection(self.line_source2.GetOutputPort())
        self.tube_filter2.SetRadius(self.settings['radius'])
        self.tube_filter2.SetNumberOfSides(20)

        tube_mapper = vtk.vtkPolyDataMapper()
        tube_mapper.SetInputConnection(self.tube_filter.GetOutputPort())

        tube_mapper1 = vtk.vtkPolyDataMapper()
        tube_mapper1.SetInputConnection(self.tube_filter1.GetOutputPort())

        tube_mapper2 = vtk.vtkPolyDataMapper()
        tube_mapper2.SetInputConnection(self.tube_filter2.GetOutputPort())

        self.tube_actor1 = vtk.vtkActor()
        self.tube_actor1.SetMapper(tube_mapper1)
        parent.renderer.AddActor(self.tube_actor1)

        self.tube_actor2 = vtk.vtkActor()
        self.tube_actor2.SetMapper(tube_mapper2)
        parent.renderer.AddActor(self.tube_actor2)


        # sp = self.tube_actor1.GetShaderProperty()
        # sp.AddFragmentShaderReplacement(
        #     "//VTK::Light::Impl",
        #     True,    # replace before VTK's own replacements
        #     """
        #     //VTK::Light::Impl
        #     float level = df > 0.85 ? 1.0 :
        #                   df > 0.55 ? 0.7  :
        #                   df > 0.25 ? 0.45 : 0.25;
        #     fragOutput0 = vec4(diffuseColorUniform * level, opacityUniform);
        #     """,
        #     False,   # only replace the first occurrence
        # )


        # sp.AddFragmentShaderReplacement(
        #     "//VTK::Light::Impl",
        #     True,
        #     """
        #     //VTK::Light::Impl
        #     float htLum = dot(fragOutput0.rgb, vec3(0.2126, 0.7152, 0.0722));

        #     float htC = cos(htAngle);
        #     float htS = sin(htAngle);
        #     mat2 htRot = mat2(htC, htS, -htS, htC);

        #     vec2 htGrid = htRot * gl_FragCoord.xy / htCellSize;
        #     float htDist = length(fract(htGrid) - 0.5);

        #     float htRadius = 0.5 * clamp(1.0 - htLum, 0.0, 1.0);
        #     float htAA = fwidth(htDist);
        #     float htInk = 1.0 - smoothstep(htRadius - htAA, htRadius + htAA, htDist);

        #     vec3 htPaper = vec3(1.0);
        #     vec3 htInkColor = diffuseColorUniform;
        #     fragOutput0.rgb = mix(htPaper, htInkColor, htInk);
        #     """,
        #     False,
        # )

        # u = sp.GetFragmentCustomUniforms()
        # u.SetUniformf("htCellSize", 10.0)
        # u.SetUniformf("htAngle", 0.7853981634)


        # sp = self.tube_actor2.GetShaderProperty()
        # sp.AddFragmentShaderReplacement(
        #     "//VTK::Light::Impl",
        #     True,    # replace before VTK's own replacements
        #     """
        #     //VTK::Light::Impl
        #     float level = df > 0.85 ? 1.0 :
        #                   df > 0.55 ? 0.7  :
        #                   df > 0.25 ? 0.45 : 0.25;
        #     fragOutput0 = vec4(diffuseColorUniform * level, opacityUniform);
        #     """,
        #     False,   # only replace the first occurrence
        # )
        
        # sp.AddFragmentShaderReplacement(
        #     "//VTK::Light::Impl",
        #     True,
        #     """
        #     //VTK::Light::Impl
        #     float htLum = dot(fragOutput0.rgb, vec3(0.2126, 0.7152, 0.0722));

        #     float htC = cos(htAngle);
        #     float htS = sin(htAngle);
        #     mat2 htRot = mat2(htC, htS, -htS, htC);

        #     vec2 htGrid = htRot * gl_FragCoord.xy / htCellSize;
        #     float htDist = length(fract(htGrid) - 0.5);

        #     float htRadius = 0.5 * clamp(1.0 - htLum, 0.0, 1.0);
        #     float htAA = fwidth(htDist);
        #     float htInk = 1.0 - smoothstep(htRadius - htAA, htRadius + htAA, htDist);

        #     vec3 htPaper = vec3(1.0);
        #     vec3 htInkColor = diffuseColorUniform;
        #     fragOutput0.rgb = mix(htPaper, htInkColor, htInk);
        #     """,
        #     False,
        # )

        # u = sp.GetFragmentCustomUniforms()
        # u.SetUniformf("htCellSize", 10.0)
        # u.SetUniformf("htAngle", 0.7853981634)

        tri_filter = vtk.vtkTriangleFilter()
        tri_filter.SetInputConnection(self.tube_filter.GetOutputPort())
        tri_filter.Update()

        silhouette = vtk.vtkPolyDataSilhouette(camera=parent.renderer.active_camera)
        silhouette.SetInputConnection(tri_filter.GetOutputPort())
        silhouette.BorderEdgesOff()
        mapper2 = vtk.vtkPolyDataMapper()
        # mapper2.SetNumberOfPieces(100)
        silhouette >> mapper2

        silhouette_tube = vtk.vtkTubeFilter()
        silhouette_tube.SetInputConnection(silhouette.GetOutputPort())
        silhouette_tube.SetRadius(self.settings['outline_radius']) 
        # silhouette_tube.SetNumberOfSides(4)
        silhouette_tube.CappingOff()

        silhouette_mapper = vtk.vtkPolyDataMapper()
        silhouette_mapper.SetInputConnection(silhouette_tube.GetOutputPort())

        self.silhouette_actor = vtk.vtkActor(mapper=silhouette_mapper)
        self.silhouette_actor.GetProperty().SetInterpolation(0)
        self.silhouette_actor.GetProperty().SetColor(self.settings['outline_color'])

        parent.renderer.AddActor(self.silhouette_actor)

        outlineMapper = vtk.vtkPolyDataMapper()
        outlineMapper.SetInputConnection(self.tube_filter.GetOutputPort())

        self._reset_properties()

        # this actor is used for drawing an outline around the atom
        self.outline_actor = vtk.vtkActor()
        self.outline_actor.SetMapper(outlineMapper)
        self.outline_actor.GetProperty().LightingOff()
        self.outline_actor.GetProperty().SetColor(vtk.vtkNamedColors().GetColor3d('Magenta'))
        # self.outline_actor.SetPosition(self.coords)

    def __str__(self):
        return self.name if self.name is not None else repr(self)

    @FloatSetting('Geometry', 'Radius', 'radius', limits=(0, float('inf')))
    def set_radius(self, radius: float = None):
        self.settings['radius'] = rcParams.get_argument('bond.radius', radius)
        self._reset_properties()

    @FloatSetting('Geometry', 'Outline Radius', 'outline_radius', limits=(0, float('inf')))
    def set_outline_radius(self, outline_radius: float = None):
        self.settings['outline_radius'] = rcParams.get_argument('bond.outline_radius', outline_radius)
        self._reset_properties()

    @BooleanSetting('Geometry', 'Draw Outline', 'outline_enabled')
    def set_outline_enabled(self, enabled: bool = None):
        self.settings['outline_enabled'] = rcParams.get_argument('bond.outline_enabled', enabled)
        self._reset_properties()

    @ColorSetting('Geometry', 'Outline Color', 'outline_color')
    def set_outline_color(self, color: Tuple[float, float, float] = None):
        self.settings['outline_color'] = rcParams.get_argument('bond.outline_color', color)
        self._reset_color()

    @FloatSetting('Material', 'Opacity', 'opacity', limits=(0, 1))
    def set_opacity(self, opacity: float = None):
        self.settings['opacity'] = rcParams.get_argument('bond.opacity', opacity)
        self._reset_properties()

    @FloatSetting('Material', 'Ambient', 'ambient', limits=(0, 1))
    def set_ambient(self, ambient: float = None):
        self.settings['ambient'] = rcParams.get_argument('bond.ambient', ambient)
        self._reset_properties()

    @FloatSetting('Material', 'Diffuse', 'diffuse', limits=(0, 1))
    def set_diffuse(self, diffuse: float = None):
        self.settings['diffuse'] = rcParams.get_argument('bond.diffuse', diffuse)
        self._reset_properties()

    @FloatSetting('Material', 'Specular', 'specular', limits=(0, 1))
    def set_specular(self, specular: float = None):
        self.settings['specular'] = rcParams.get_argument('bond.specular', specular)
        self._reset_properties()

    @FloatSetting('Material', 'Specular Power', 'specular_power', limits=(0, float('inf')))
    def set_specular_power(self, specular_power: float = None):
        self.settings['specular_power'] = rcParams.get_argument('bond.specular_power', specular_power)
        self._reset_properties()

    @ColorSetting('Material', 'Color', 'color')
    def set_color(self, color: Tuple[float, float, float] = None):
        self.settings['color'] = rcParams.get_argument('bond.color', color)
        self._reset_color()

    @BooleanSetting('Material', 'Use Atom Colors', 'use_atom_colors')
    def set_use_atom_colors(self, enable: bool = None):
        self.settings['use_atom_colors'] = rcParams.get_argument('bond.use_atom_colors', enable)
        self._reset_color()

    def _reset_properties(self):
        self.tube_filter1.SetRadius(self.settings['radius'])
        self.tube_filter2.SetRadius(self.settings['radius'])
        self.tube_filter.SetRadius(self.settings['radius'])

        self.silhouette_actor.SetVisibility(self.settings['outline_enabled'])

        self.tube_actor1.GetProperty().SetOpacity(self.settings['opacity'])
        self.tube_actor1.GetProperty().SetAmbient(self.settings['ambient'])
        self.tube_actor1.GetProperty().SetDiffuse(self.settings['diffuse'])
        self.tube_actor1.GetProperty().SetSpecular(self.settings['specular'])
        self.tube_actor1.GetProperty().SetSpecularPower(self.settings['specular_power'])

        self.tube_actor2.GetProperty().SetOpacity(self.settings['opacity'])
        self.tube_actor2.GetProperty().SetAmbient(self.settings['ambient'])
        self.tube_actor2.GetProperty().SetDiffuse(self.settings['diffuse'])
        self.tube_actor2.GetProperty().SetSpecular(self.settings['specular'])
        self.tube_actor2.GetProperty().SetSpecularPower(self.settings['specular_power'])
        # parent.renderer.GetRenderWindow().Render()

        self._reset_color()

    def _reset_color(self):
        if self.settings['use_atom_colors']:
            atom1 = self.parent.match_plams_to_shape(self.a1)
            atom2 = self.parent.match_plams_to_shape(self.a2)
            self.tube_actor1.GetProperty().SetColor([x/255 for x in atom1.get_color()])
            self.tube_actor2.GetProperty().SetColor([x/255 for x in atom2.get_color()])
        else:
            self.tube_actor1.GetProperty().SetColor(self.settings['color'])
            self.tube_actor2.GetProperty().SetColor(self.settings['color'])

        self.silhouette_actor.GetProperty().SetColor(self.settings['outline_color'])
