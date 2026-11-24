import tcviewer
import pyfmo


orbs = pyfmo.orbitals2.objects.Orbitals('/Users/yumanhordijk/Downloads/adf.rkf')

orb = orbs.mos['HOMO']

with tcviewer.Screen() as screen:
    with screen.add_molscene() as scene:          
        c1, c2 = ([1, 0, 0], [0, 0, 1]) if orb.occupied else ([1, .5, 0], [0, 1, 1])
        scene.draw_molecule(orbs.molecule)
        scene.draw_dual_isosurface(orb.cube_file(), colorm=c1, colorp=c2, opacity=.3)
        scene.draw_text(str(orb))
