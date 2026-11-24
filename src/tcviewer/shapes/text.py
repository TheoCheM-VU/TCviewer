from typing import List, Tuple, Union
import vtk
from tcviewer import shapes


class ScreenText(shapes.EditableShape):
    def __init__(
        self, 
        renderer: vtk.vtkRenderer, 
        text: str,
        position: Tuple[float] = (0, 0),
        hjust: str = 'left',
        vjust: str = 'bottom',
        font_size: int = 24,
        color: Tuple[int] = (255, 255, 255),
        **kwargs
    ):
        super().__init__(**kwargs)
        self.renderer = renderer

        self.text_actor = vtk.vtkTextActor()
        self.text_actor.SetInput(text)
        
        self.text_actor.SetPosition(position)

        self.text_actor.UseBorderAlignOff()
        self.text_actor.GetTextProperty().SetFontSize(font_size)
        self.text_actor.GetTextProperty().SetColor(color)

        if hjust == 'right':
            self.text_actor.GetTextProperty().SetJustificationToRight()
        if hjust == 'centered':
            self.text_actor.GetTextProperty().SetJustificationToCentered()
        if hjust == 'left':
            self.text_actor.GetTextProperty().SetJustificationToLeft()

        if vjust == 'bottom':
            self.text_actor.GetTextProperty().SetVerticalJustificationToBottom()
        if vjust == 'centered':
            self.text_actor.GetTextProperty().SetVerticalJustificationToCentered()
        if vjust == 'top':
            self.text_actor.GetTextProperty().SetVerticalJustificationToTop()

        self.renderer.AddActor2D(self.text_actor)
