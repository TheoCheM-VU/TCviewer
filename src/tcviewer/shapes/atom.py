from typing import Tuple, Union
import vtk
import tcmu
from tcviewer import (
    shapes, 
    FloatSetting, 
    ColorSetting, 
    CategorySetting, 
    BooleanSetting,
    rcParams, 
    get_atom_radius_conventions, 
    get_atom_radius, 
    get_atom_color_conventions,
    get_atom_color,)
import numpy as np


class AtomSpecificData:
    ...


class AtomSpecificRadius(AtomSpecificData):
    def __call__(self, atom: 'Atom'):
        return tcmu.data.atom.radius(atom.symbol)


class AtomSpecificColorR(AtomSpecificData):
    def __call__(self, atom: 'Atom'):
        return tcmu.data.atom.color(atom.symbol)[0]/255


class AtomSpecificColorG(AtomSpecificData):
    def __call__(self, atom: 'Atom'):
        return tcmu.data.atom.color(atom.symbol)[1]/255


class AtomSpecificColorB(AtomSpecificData):
    def __call__(self, atom: 'Atom'):
        return tcmu.data.atom.color(atom.symbol)[2]/255


class Atom(shapes.EditableShape):
    def __init__(
        self, 
        parent,
        atom_type: Union[str, int], 
        coords: Tuple[float, float, float],
        name: str = None,

        radius: float = None,
        radius_convention: str = None,
        scale: float = None,
        color: Tuple[int, int, int] = None,
        color_convention: str = None,
        quadrant_crossing: Tuple[float, float] = None,
        quadrant_width: float = None,
        quadrants_enabled: bool = None,
        outline_width: float = None,
        outline_enabled: bool = None,

        opacity: float = None,
        ambient: float = None,
        diffuse: float = None,
        specular: float = None,
        specular_power: float = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.parent = parent
        self.symbol = tcmu.data.atom.symbol(atom_type)
        self.coords = coords
        self.name = name

        # settings holds all properties related to this atom shape
        self.settings = {}

        self.settings['radius']             = radius
        self.settings['radius_convention']  = rcParams.get_argument('atom.radius_convention', radius_convention)
        self.settings['scale']              = rcParams.get_argument('atom.scale', scale)
        self.settings['quadrant_crossing']  = rcParams.get_argument('atom.quadrant_crossing', quadrant_crossing)
        self.settings['quadrant_width']     = rcParams.get_argument('atom.quadrant_width', quadrant_width)
        self.settings['quadrants_enabled']  = rcParams.get_argument('atom.quadrants_enabled', quadrants_enabled)
        self.settings['outline_width']      = rcParams.get_argument('atom.outline_width', outline_width)
        self.settings['outline_enabled']    = rcParams.get_argument('atom.outline_enabled', outline_enabled)
        self.settings['color']              = color
        self.settings['color_convention']   = rcParams.get_argument('atom.color_convention', color_convention)

        self.settings['opacity']            = rcParams.get_argument('atom.opacity', opacity)
        self.settings['ambient']            = rcParams.get_argument('atom.ambient', ambient)
        self.settings['diffuse']            = rcParams.get_argument('atom.diffuse', diffuse)
        self.settings['specular']           = rcParams.get_argument('atom.specular', specular)
        self.settings['specular_power']     = rcParams.get_argument('atom.specular_power', specular_power)

        def draw_arc(p, n, a):
            arc = vtk.vtkArcSource()
            arc.UseNormalAndAngleOn()
            arc.SetNormal(n)
            arc.SetPolarVector(p)
            arc.SetAngle(a)
            arc.SetResolution(40)

            ribbon_filter = vtk.vtkRibbonFilter(angle=90)
            ribbon_filter.source = arc
            ribbon_filter.SetInputConnection(arc.GetOutputPort())
            ribbon_filter.SetWidth(self.settings['quadrant_width'])

            arc_mapper = vtk.vtkPolyDataMapper()
            arc_mapper.SetInputConnection(ribbon_filter.GetOutputPort())

            arc_actor = vtk.vtkFollower()
            arc_actor.SetCamera(parent.renderer.GetActiveCamera())
            arc_actor.SetPosition(coords)
            arc_actor.SetMapper(arc_mapper)
            arc_actor.PickableOff()
            parent.renderer.AddActor(arc_actor)

            return arc, ribbon_filter, arc_actor

        def draw_circle(c, r):
            points = vtk.vtkPoints()
            for i in range(41):
                angle = 2 * np.pi / 39 * i
                points.InsertNextPoint(-r*np.sin(angle), r*np.cos(angle), 0)

            poly_line = vtk.vtkCellArray()
            poly_line.InsertNextCell(41)
            for i in range(41):
                poly_line.InsertCellPoint(i)

            # Create a polydata to store everything in
            poly_data = vtk.vtkPolyData()
            poly_data.SetPoints(points)
            poly_data.SetLines(poly_line)

            circle_filter = vtk.vtkTubeFilter()
            circle_filter.SetInputData(poly_data)
            circle_filter.SetRadius(self.settings['outline_width'])
            circle_filter.SetNumberOfSides(20)
            circle_filter.CappingOff()
            circle_filter.Update()

            circle_mapper = vtk.vtkPolyDataMapper()
            circle_mapper.SetInputConnection(circle_filter.GetOutputPort())

            circle_actor = vtk.vtkFollower()
            circle_actor.SetCamera(parent.renderer.GetActiveCamera())
            circle_actor.SetPosition(coords)
            circle_actor.SetMapper(circle_mapper)
            circle_actor.PickableOff()
            parent.renderer.AddActor(circle_actor)

            return poly_data, circle_filter, circle_actor

        self.sphere = vtk.vtkSphereSource()
        self.sphere.SetPhiResolution(35)
        self.sphere.SetThetaResolution(45)
        self.sphere.SetRadius(self.get_radius() * self.settings['scale'])
        self.sphere_mapper = vtk.vtkPolyDataMapper()
        self.sphere_mapper.SetInputConnection(self.sphere.GetOutputPort())
        self.sphere_actor = vtk.vtkActor()
        self.sphere_actor.SetMapper(self.sphere_mapper)
        self.sphere_actor.SetPosition(coords)
        self.sphere_actor.GetProperty().BackfaceCullingOn()


        sp = self.sphere_actor.GetShaderProperty()
        levels = ""
        Nlevels = 2
        minimum_light = 0.3
        for i in range(Nlevels):
            print((Nlevels - i)/Nlevels)
            levels += f"df > {(Nlevels - i - 1)/Nlevels} ? {(Nlevels - i)/Nlevels*(1 - minimum_light) + minimum_light} :\n"
        levels += f"{minimum_light}"

        # shader = f"""
        #     //VTK::Light::Impl
        #     float level = {levels};
        #     fragOutput0 = vec4(diffuseColorUniform * level, opacityUniform);
        # """
        # print(shader)

        # sp.AddFragmentShaderReplacement(
        #     "//VTK::Light::Impl",
        #     True,    # replace before VTK's own replacements
        #     shader,
        #     False,   # only replace the first occurrence
        # )

        # sp = self.sphere_actor.GetShaderProperty()

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

        #     float htRadius = 0.5 * pow(clamp(1.0 - htLum, 0.0, 1.0), 2.0);
        #     float htAA = fwidth(htDist);
        #     float htInk = 1.0 - smoothstep(htRadius - htAA, htRadius + htAA, htDist);

        #     vec3 htPaper = diffuseColorUniform;
        #     vec3 htInkColor = diffuseColorUniform/2;
        #     fragOutput0.rgb = mix(htPaper, htInkColor, htInk);
        #     """,
        #     False,
        # )

        # u = sp.GetFragmentCustomUniforms()
        # u.SetUniformf("htCellSize", 13.0)
        # u.SetUniformf("htAngle", 1.3)



        self.settings['outline_color'] = [0, 0, 0]
        parent.renderer.AddActor(self.sphere_actor)

        # increase r slightly to solve z-fighting issues with the sphere
        r = self.get_radius() * self.settings['scale'] * 1.001
        self.outline_circle, self.outline_ribbon_filter, self.outline_circle_actor = draw_circle([0, 0, 0], r)

        p = [0.5, -0.5, None]
        p[2] = np.sqrt(1 - p[0]**2 - p[1]**2)

        n1 = np.cross(p, [r, 0, 0])
        n2 = np.cross(p, [0, r, 0])

        self.quadrant_arc1, self.quadrant_ribbon_filter1, self.quadrant_arc1_actor = draw_arc([r, 0, 0], n1, -180)
        self.quadrant_arc2, self.quadrant_ribbon_filter2, self.quadrant_arc2_actor = draw_arc([0, r, 0], n2, -180)

        self._reset_properties()

        # this actor is used for drawing an outline around the atom
        self.outline_actor = vtk.vtkActor()
        self.outline_actor.SetMapper(self.sphere_mapper)
        self.outline_actor.GetProperty().LightingOff()
        self.outline_actor.GetProperty().SetColor(vtk.vtkNamedColors().GetColor3d('Magenta'))
        self.outline_actor.SetPosition(self.coords)


    def __str__(self):
        return self.name if self.name is not None else repr(self)


    @FloatSetting('Geometry', 'Radius', 'radius', limits=(0, float('inf')))
    def set_radius(self, radius: float = None):
        self.settings['radius'] = radius
        self._reset_properties()


    @CategorySetting('Geometry', 'Radius', 'radius_convention', get_atom_radius_conventions)
    def set_radius_convention(self, convention: str = None):
        self.settings['radius_convention'] = rcParams.get_argument('atom.radius_convention', convention)
        self._reset_properties()


    def get_radius(self) -> float:
        if self.settings['radius'] is None:
            return get_atom_radius(self.symbol, self.settings['radius_convention'])
        else:
            return self.settings['radius']


    @FloatSetting('Geometry', 'Scale', 'scale', limits=(0, float('inf')))
    def set_scale(self, scale: float = None):
        self.settings['scale'] = rcParams.get_argument('atom.scale', scale)
        self._reset_properties()


    @FloatSetting('Geometry', 'Quadrant Crossing', 'quadrant_crossing', limits=[(-1, 1), (-1, 1)])
    def set_quadrant_crossing(self, c: Tuple[float, float] = None):
        self.settings['quadrant_crossing'] = rcParams.get_argument('atom.quadrant_crossing', c)
        self._reset_quadrants()


    @FloatSetting('Geometry', 'Quadrant Width', 'quadrant_width', limits=(0, float('inf')))
    def set_quadrant_width(self, width: float = None):
        self.settings['quadrant_width'] = rcParams.get_argument('atom.quadrant_width', width)
        self._reset_quadrants()


    @BooleanSetting('Geometry', 'Draw Quadrants', 'quadrants_enabled')
    def set_quadrants_enabled(self, enable: bool = None):
        self.settings['quadrants_enabled'] = rcParams.get_argument('atom.quadrants_enabled', enable)
        self._reset_quadrants()


    @FloatSetting('Geometry', 'Draw Outline', 'outline_width', limits=(0, float('inf')))
    def set_outline_width(self, width: float = None):
        self.settings['outline_width'] = rcParams.get_argument('atom.outline_width', width)
        self._reset_outline()


    @BooleanSetting('Geometry', 'Draw Outline', 'outline_enabled')
    def set_outline_enabled(self, enable: bool = None):
        self.settings['outline_enabled'] = rcParams.get_argument('atom.outline_enabled', enable)
        print(self.settings['outline_enabled'])
        self._reset_outline()


    @FloatSetting('Material', 'Opacity', 'opacity', limits=(0, 1))
    def set_opacity(self, opacity: float = None):
        self.settings['opacity'] = rcParams.get_argument('atom.opacity', opacity)
        for actor in [self.sphere_actor, self.outline_circle_actor, self.quadrant_arc1_actor, self.quadrant_arc2_actor]:
            actor.GetProperty().SetOpacity(self.settings['opacity'])


    @FloatSetting('Material', 'Ambient', 'ambient', limits=(0, 1))
    def set_ambient(self, ambient: float = None):
        self.settings['ambient'] = rcParams.get_argument('atom.ambient', ambient)
        self.sphere_actor.GetProperty().SetAmbient(self.settings['ambient'])


    @FloatSetting('Material', 'Diffuse', 'diffuse', limits=(0, 1))
    def set_diffuse(self, diffuse: float = None):
        self.settings['diffuse'] = rcParams.get_argument('atom.diffuse', diffuse)
        self.sphere_actor.GetProperty().SetDiffuse(self.settings['diffuse'])


    @FloatSetting('Material', 'Specular', 'specular', limits=(0, 1))
    def set_specular(self, specular: float = None):
        self.settings['specular'] = rcParams.get_argument('atom.specular', specular)
        self.sphere_actor.GetProperty().SetSpecular(self.settings['specular'])


    @FloatSetting('Material', 'Specular Power', 'specular_power', limits=(0, float('inf')))
    def set_specular_power(self, specular_power: float = None):
        self.settings['specular_power'] = rcParams.get_argument('atom.specular_power', specular_power)
        self.sphere_actor.GetProperty().SetSpecularPower(self.settings['specular_power'])


    @ColorSetting('Material', 'Color', 'color')
    def set_color(self, color: Tuple[int, int, int] = None):
        self.settings['color'] = color
        self.sphere_actor.GetProperty().SetColor([c/255 for c in self.get_color()])
        for bond in self.parent.find_bonds(self):
            bond._reset_color()


    def get_color(self) -> Tuple[int, int, int]:
        if self.settings['color'] is None:
            return get_atom_color(self.symbol, self.settings['color_convention'])
        else:
            return self.settings['color']


    @CategorySetting('Material', 'Color Convention', 'color_convention', options=get_atom_color_conventions)
    def set_color_convention(self, convention: str = None):
        self.settings['color_convention'] = rcParams.get_argument('atom.color_convention', convention)
        self.sphere_actor.GetProperty().SetColor([c/255 for c in self.get_color()])
        for bond in self.parent.find_bonds(self):
            bond._reset_color()


    @ColorSetting('Material', 'Outline Color', 'outline_color')
    def set_outline_color(self, color: Tuple[int, int, int] = None):
        self.settings['outline_color'] = rcParams.get_argument('atom.outline_color', color)
        self._reset_properties()


    def _reset_properties(self):
        self.sphere.SetRadius(self.get_radius() * self.settings['scale'])
        self._reset_quadrants()
        self._reset_outline()

        self.sphere_actor.GetProperty().SetColor([c/255 for c in self.get_color()])
        self.outline_circle_actor.GetProperty().SetColor(self.settings['outline_color'])
        self.quadrant_arc1_actor.GetProperty().SetColor(self.settings['outline_color'])
        self.quadrant_arc2_actor.GetProperty().SetColor(self.settings['outline_color'])


    def _reset_quadrants(self):
        if not self.settings['quadrants_enabled']:
            self.quadrant_arc1_actor.VisibilityOff()
            self.quadrant_arc2_actor.VisibilityOff()
            return

        self.quadrant_arc1_actor.VisibilityOn()
        self.quadrant_arc2_actor.VisibilityOn()
        r = self.get_radius() * self.settings['scale'] * 1.001

        p = [self.settings['quadrant_crossing'][0], self.settings['quadrant_crossing'][1], None]

        p[2] = np.sqrt(1 - p[0]**2 - p[1]**2)

        n1 = np.cross(p, [r, 0, 0])
        n2 = np.cross(p, [0, r, 0])

        self.quadrant_arc1.SetNormal(n1)
        self.quadrant_arc2.SetNormal(n2)
        self.quadrant_arc1.SetPolarVector([r, 0, 0])
        self.quadrant_arc2.SetPolarVector([0, r, 0])
        self.quadrant_ribbon_filter1.SetWidth(self.settings['quadrant_width'])
        self.quadrant_ribbon_filter2.SetWidth(self.settings['quadrant_width'])


    def _reset_outline(self):
        if not self.settings['outline_enabled']:
            self.outline_circle_actor.VisibilityOff()
            return

        self.outline_circle_actor.VisibilityOn()

        r = self.get_radius() * self.settings['scale'] * 1.001

        points = vtk.vtkPoints()
        for i in range(41):
            angle = 2 * np.pi / 39 * i
            points.InsertNextPoint(-r*np.sin(angle), r*np.cos(angle), 0)

        self.outline_circle.SetPoints(points)
        self.outline_ribbon_filter.SetRadius(self.settings['outline_width'])
