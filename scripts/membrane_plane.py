# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 16:56:22 2021

@author: Laura Xénard
"""

import argparse
from pathlib import Path
import time

from Bio.PDB import PDBParser
from Bio.PDB.DSSP import DSSP
from mayavi import mlab
import numpy as np

import protein as ptn


def barycenter(residues_list):
    """
    Compute the barycenter of a list of residues.

    Parameters
    ----------
    residues_list : list(ptn.Residues)
        The residues from which to find the barycenter.

    Returns
    -------
    x_bary, y_bary, z_bary : (float, float, float)
        Respectively x, y and z coordinates of the residues barycenter.

    """
    x_bary = sum([r.coord.x for r in residues_list]) / len(residues_list)
    y_bary = sum([r.coord.y for r in residues_list]) / len(residues_list)
    z_bary = sum([r.coord.z for r in residues_list]) / len(residues_list)
    return x_bary, y_bary, z_bary


if __name__ == '__main__':

    start = time.time()

    # TODO: Argument à sortir par argparse
    pdb_path = 'G:/RAID/Fac/M2_BI/PGP/CompBio/data/2n90.pdb'
    model = 0
    chain = 'A'
    IS_EXPOSED_THRESHOLD = 0.3
    DEBUG = False
    N_DIRECTIONS = 20 # nb de points pour échantillonner la demi-sphère

    # Opening and parsing of the PDB file.
    p = PDBParser()
    ptn_id = Path(pdb_path).stem
    structure = p.get_structure(ptn_id, pdb_path)
    dssp = DSSP(structure[model], pdb_path)

    # Selection of the exposed residues.
    # For better results, the burrowed residues are not taken into account
    # during the membrane detection.
    # TODO: à vérifier en comparant les résultats avec le traitement de tous
    # les résidus
    residues = []  # Store the exposed residues.
    for i_res, res in enumerate(structure[model][chain]):
        # For simplification, the position of a residue is defined as the
        # position of its Cα.
        pt = ptn.Point(*res['CA'].coord)
        asa = dssp[(chain, i_res+1)][3]  # Accessible surface area.
        tmp = ptn.Residue(res.id[1], res.resname, pt, asa)
        if tmp.is_exposed(IS_EXPOSED_THRESHOLD):
            residues.append(tmp)

    # Place the center of the coordinate system at the residues barycenter.
    bary = ptn.Point(*barycenter(residues))
    if DEBUG:
        print(f"Barycenter: {bary}")
    for res in residues:
        res.coord -= bary

    # Sample the space in roughly N_DIRECTIONS vectors all passing by the
    # center of the coordinate system center.
    sphere = ptn.Sphere()
    sphere.sample_surface(N_DIRECTIONS*2)


    # Create a sphere
    pi = np.pi
    cos = np.cos
    sin = np.sin
    phi, theta = np.mgrid[0:pi:101j, 0:2 * pi:101j]

# =============================================================================
#     x = sin(phi)*cos(theta)
#     y = sin(phi)*sin(theta)
#     z = cos(phi)
# =============================================================================

    mlab.figure(1, bgcolor=(1, 1, 1), fgcolor=(0, 0, 0), size=(600, 600))
    mlab.clf()

    #mlab.mesh(x , y , z, color=(0.0,0.5,0.5))
    mlab.points3d(0, 0, 0, scale_factor=0.1, color=(1, 0, 0))
    vectors = []
    for point in sphere.surf_pts:
        mlab.points3d(point.x, point.y, point.z, scale_factor=0.05)
        v = ptn.Vector(point)
# =============================================================================
#         mlab.plot3d(v.get_xx(), v.get_yy(), v.get_zz(), color=(0, 0, 1),
#                     tube_radius=None)
# =============================================================================
        vectors.append(v)
    #mlab.show()

    mlab.plot3d(v.get_xx(), v.get_yy(), v.get_zz(), color=(0, 1, 0),
                    tube_radius=None)

    slices = []
    # obtenir les plans orthogonaux
    for v in vectors:
        s = ptn.Slice(0, v)
        slices.append(s)

    for res in residues:
        mlab.points3d(res.coord.x, res.coord.y, res.coord.z,
                      scale_factor=1, color=(0.5, 0, 0.5))


    a = slices[0].normal.end.x
    b = slices[0].normal.end.y
    c = slices[0].normal.end.z
    x, y = np.mgrid[-20:20:1000j, -20:20:1000j]
    z = (-a*x - b*y + -7) / c
    zz = (-a*x - b*y + 7) / c
    mlab.surf(x, y, z)
    mlab.surf(x, y, zz)

    for s, sli in enumerate(slices):
        sli.find_residues(residues)
        try:
            sli.compute_score()
        except ValueError:
            print("Method must be 'ASA' or 'simple'")
        print(f"Score slice {s} : {sli.score}")

    mlab.show()

# =============================================================================
#     for s, sli in enumerate(slices):
#         sli.find_residues(residues)
#         sli.compute_score()
#         print(f"Score slice {s} : {sli.score}")
# =============================================================================

    print(max(slices))


    # obtenir les plans translatés
# =============================================================================
#     slices[0].find_residues(residues)
#     for res in slices[0].residues:
#         mlab.points3d(res.coord.x, res.coord.y, res.coord.z,
#                       scale_factor=1.1, color=(0, 1, 0))
#
#     mlab.show()
#     slices[0].compute_score()
#     print(f"Score slice 0 : {slices[0].score}")
# =============================================================================











    # TODO: pour le renvoi des résultats, ne pas oublier de translater
    # la membrane puisuqe le centre du repère a été déplacé sur le barycentre

    end = time.time() - start
    print('\nDONE in {:.0f} min {:.2f} s.'.format(end // 60, end % 60))