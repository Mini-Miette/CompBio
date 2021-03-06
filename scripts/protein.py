# -*- coding: utf-8 -*-
"""
Created on Sun Sep  5 16:55:30 2021
@author: Laura Xénard

This module defines the following classes used in membrane_plane.py:
    * some geometrical ones:
        - Point
        - Vector
        - Sphere
    * and some biological ones:
        - Residue
        - Protein
        - Slice
"""


import math
import warnings

from Bio.PDB import Dice
from Bio.PDB.DSSP import DSSP
import Bio.PDB.Atom
from Bio.PDB.PDBExceptions import PDBConstructionWarning
import Bio.PDB.Residue
import numpy as np

import settings as st



class Point:
    """
    Represent a point in 3D space.

    Parameters
    ----------
    x : float, optional
        The x coordinate. The default is 0.
    y : float, optional
        The y coordinate. The default is 0.
    z : float, optional
        The z coordinate. The default is 0.

    Attributes
    ----------
    x : float
        The x coordinate.
    y : float
        The y coordinate.
    z : float
        The z coordinate.

    """
    def __init__(self, x=0, y=0, z=0):
        self.x = x
        self.y = y
        self.z = z

    def __repr__(self):
        return f"[{self.x}, {self.y}, {self.z}]"

    def __add__(self, p):
        x = self.x + p.x
        y = self.y + p.y
        z = self.z + p.z
        return Point(x, y, z)

    def __sub__(self, p):
        x = self.x - p.x
        y = self.y - p.y
        z = self.z - p.z
        return Point(x, y, z)

    def __neg__(self):
        x = -self.x
        y = -self.y
        z = -self.z
        return Point(x, y, z)


    @classmethod
    def barycenter(cls, residues_list):
        """
        Compute the barycenter of a list of residues.

        Parameters
        ----------
        residues_list : list(ptn.Residues)
            The residues from which to find the barycenter.

        Returns
        -------
        Point
            The barycenter of the Residues.

        """
        x_bary = sum([r.coord.x for r in residues_list]) / len(residues_list)
        y_bary = sum([r.coord.y for r in residues_list]) / len(residues_list)
        z_bary = sum([r.coord.z for r in residues_list]) / len(residues_list)
        return Point(x_bary, y_bary, z_bary)


class Vector:
    """
    Represent a vector in 3D space.

    Parameters
    ----------
    end : Point
        The end point of the vector.

    Attributes
    ----------
    start : Point
        The start point of the vector.
    end : Point
        The end point of the vector.

    """
    start = Point(0, 0, 0)

    def __init__(self, end):
        self.end = end

    def __repr__(self):
        return f"(start: {self.start}, end: {self.end})"

    def get_xx(self):
        """
        Getter for the x coordinates.

        Returns
        -------
        list
            x coordinates of the Vector.

        """
        return [self.start.x, self.end.x]

    def get_yy(self):
        """
        Getter for the y coordinates.

        Returns
        -------
        list
            y coordinates of the Vector.

        """
        return [self.start.y, self.end.y]

    def get_zz(self):
        """
        Getter for the z coordinates.

        Returns
        -------
        list
            z coordinates of the Vector.

        """
        return [self.start.z, self.end.z]


class Sphere:
    """
    Represent a sphere in 3D space.

    Parameters
    ----------
    radius : int, optional
            Radius of the sphere. The default is 1.

    Attributes
    ----------
    origin : Point
        The center of the sphere.
    radius : int
            Radius of the sphere.
    surf_pts : list(Point)
            Points on the surface of the Sphere.

    """
    origin = Point(0, 0, 0)

    def __init__(self, radius=1):
        self.radius = radius
        self.surf_pts = []

    def sample_surface(self, nb):
        """
        Generate equidistributed Points on the surface of the demi Sphere.

        The Points are generated on the z-positive part of the Sphere.

        Parameters
        ----------
        nb : int
            The ideal number of Points to be generated. In some cases, less
            Points might be generated.

        Raises
        ------
        ValueError
            Raised when the number of Points to generate is inferior or equal
            to 0.

        Returns
        -------
        int
            The number of Points that have been generated. It may not be
            exactly equal to 'nb' but should be close to it.

        Notes
        -----
        This code implements the Deserno algorithm:
        https://www.cmu.edu/biolphys/deserno/pdf/sphere_equi.pdf
        and is based on dinob0t's code:
        https://gist.github.com/dinob0t/9597525

        """
        if nb <= 0:
            raise ValueError

        a = 4.0 * math.pi * (self.radius**2.0 / nb)
        d = math.sqrt(a)
        m_theta = int(round(math.pi / d))
        d_theta = math.pi / m_theta
        d_phi = a / d_theta

        for m in range(0, m_theta):
            theta = math.pi * (m + 0.5) / m_theta
            m_phi = int(round(2.0 * math.pi * math.sin(theta) / d_phi))
            for n in range(0, m_phi):
                phi = 2.0 * math.pi * n / m_phi
                x = self.radius * math.sin(theta) * math.cos(phi)
                y = self.radius * math.sin(theta) * math.sin(phi)
                z = self.radius * math.cos(theta)
                if z >= 0:
                    self.surf_pts.append(Point(x, y, z))
        return len(self.surf_pts)


class Residue:
    """
    Represent a protein residue.

    Parameters
    ----------
    num : int, optional
        Position in the protein. The default is 0.
    aa : str, optional
        3 letters designation of the type of residue. The default is ''.
    p : Point, optional
        Position in 3D space. The default is Point().
    asa : 0, optional
        Accessible surface area. The default is 0.

    Attributes
    ----------
    num : int
        Position in the protein.
    aa : str
        3 letters designation of the type of residue.
    coord : Point
        Position in 3D space.
    asa : 0
        Accessible surface area.

    """
    def __init__(self, num=0, aa='', p=Point(), asa=0):
        self.num = num
        self.aa = aa
        self.coord = p
        self.asa = asa

    def __repr__(self):
        return f"({self.num}, {self.aa}, coord: {self.coord}, asa: {self.asa})"

    def is_hydrophobic(self):
        """
        Determine if the residue is hydrophobic or not.

        Raises
        ------
        ValueError
            Raised when the amino acid of the residue is not valid.

        Returns
        -------
        bool
            True if the residue is hydrophobic, False otherwise.

        """
        hydrophobic = ('PHE', 'GLY', 'ILE', 'LEU', 'MET', 'VAL', 'TRP', 'TYR')
        hydrophilic = ('ALA', 'CYS', 'ASP', 'GLU', 'HIS', 'LYS', 'ASN', 'PRO',
                       'GLN', 'ARG', 'SER', 'THR')
        if self.aa not in hydrophobic and self.aa not in hydrophilic:
            raise ValueError

        if self.aa in hydrophobic:
            return True
        else:
            return False

    def is_exposed(self, threshold=0.3):
        """
        Determine if the residue is exposed to solvent or burrowed.

        Parameters
        ----------
        threshold : float, optional
            Threshold defining is a residue is exposed or burrowed. The
            default is 0.3.

        Returns
        -------
        bool
            True if the residue is exposed to solvent or membrane, False if
            it is burrowed in the protein.

        """
        if self.asa >= threshold:
            return True
        else:
            return False


class Protein():
    """
    Represent a protein.

    Parameters
    ----------
    structure : Bio.PDB.Structure
        Protein structure parsed from a pdb file.
    model : Bio.PDB.Model, optional
        ID of the model on which to work. The default is 0.
    chain : Bio.PDB.Chain, optional
        ID of the chain on which to work. The default is 'A'.
    first_residue : int, optional
        ID of first residue to consider. The default is None.
    last_residue : int, optional
        ID of last residue to consider. The default is None.

    Attributes
    ----------
    structure : Bio.PDB.Structure
        Protein structure parsed from a pdb file.
    model : Bio.PDB.Model
        ID of the model on which to work. The default is 0.
    chain : Bio.PDB.Chain
        ID of the chain on which to work. The default is 'A'.
    res_ids_pdb : list(int)
        PDB IDs of the residues to consider.
    vectors : list(Vector)
        Vectors sampling the 3D space.
    residues_burrowed : list(Residue)
        Residues not exposed to solvent or membrane.
    residues_exposed : list(Residue)
        Residues exposed to solvent or membrane.
    residues_exposed_hydrophobic : list(Residue)
        Hydrophobic Residues exposed to solvent or membrane.

    """
    def __init__(self, structure, model=0, chain='A', first_residue=None,
                 last_residue=None):
        self.structure = structure

        models = [m.id for m in structure.get_models()]
        if model in models:
            self.model = model
        else:
            self.model = models[0]
            print(f"WARNING: model {model} does not exist. Using the first "
                  f"model found instead which is {self.model}.")

        chains = [c.id for c in structure[self.model].get_chains()]
        if chain in chains:
            self.chain = chain
        else:
            self.chain = chains[0]
            print(f"WARNING: chain {chain} does not exist. Using the first "
                  f"chain found instead which is {self.chain}.")

        ids = [d.get_id()[1] for d in structure[self.model][self.chain]]
        if (first_residue is None) and (last_residue is None):
            self.res_ids_pdb = ids
        elif last_residue is None:
            try:
                first_index = ids.index(first_residue)
                self.res_ids_pdb = ids[first_index:]
            except (ValueError, IndexError):
                print(f"WARNING: residue {first_residue} does not exist in "
                      f"model {self.model} chain {self.chain}. "
                      "Starting from the first existing residue instead"
                      f" which is {ids[0]}.")
                self.res_ids_pdb = ids
        elif first_residue is None:
            try:
                last_index = ids.index(last_residue)
                self.res_ids_pdb = ids[:last_index]
            except (ValueError, IndexError):
                print(f"WARNING: residue {last_residue} does not exist in "
                      f"model {self.model} chain {self.chain}. "
                      "Starting from the last existing residue instead"
                      f" which is {ids[-1]}.")
                self.res_ids_pdb = ids
        else:
            try:
                first_index = ids.index(first_residue)
            except (ValueError, IndexError):
                print(f"WARNING: residue {first_residue} does not exist in "
                      f"model {self.model} chain {self.chain}. "
                      "Starting from the first existing residue instead"
                      f" which is {ids[0]}.")
                first_index = 0
            try:
                last_index = ids.index(last_residue) + 1
            except (ValueError, IndexError):
                print(f"WARNING: residue {last_residue} does not exist in "
                      f"model {self.model} chain {self.chain}. "
                      "Starting from the last existing residue instead"
                      f" which is {ids[-1]}.")
                last_index = len(ids)
            self.res_ids_pdb = ids[first_index:last_index]

        self.vectors = []
        self.sample_space()

        self.residues_burrowed = []
        self.residues_exposed = []
        self.find_exposed_residues()

        self.residues_exposed_hydrophobic = []
        self.find_exposed_hydrophobic_residues()

    def sample_space(self):
        """
        Sample the space in several vectors.

        All the vectors pass by the center of the coordinate system.

        Returns
        -------
        None.

        """
        sphere = Sphere()
        sphere.sample_surface(st.N_DIRECTIONS*2)
        for point in sphere.surf_pts:
            self.vectors.append(Vector(point))

    def find_exposed_residues(self):
        """
        Find the residues exposed to solvent or membrane.

        Returns
        -------
        None.

        """
        dssp = DSSP(self.structure[self.model], st.PDB)
        for i_res in self.res_ids_pdb:
            # For simplification, the position of a residue is defined as the
            # position of its Cα.
            res = self.structure[self.model][self.chain][i_res]
            try:
                pt = Point(*res['CA'].coord)
            except KeyError:
                print(f"WARNING: no Cα found for residue {i_res} "
                      f"({res.resname}), meaning it's probably not a "
                      "standard amino acid. Ignoring this residue for "
                      "the rest of the analysis.")
            else:
                asa = dssp[(self.chain, i_res)][3]  # Accessible surface area.
                tmp = Residue(res.id[1], res.resname, pt, asa)
                if tmp.is_exposed(st.IS_EXPOSED_THRESHOLD):
                    self.residues_exposed.append(tmp)
                else:
                    # Save burrowed residues in case they are needed later.
                    self.residues_burrowed.append(tmp)

    def find_exposed_hydrophobic_residues(self):
        """
        Find all the hydrophobic residues.

        Returns
        -------
        None.

        """
        for res in self.residues_exposed:
            try:
                if res.is_hydrophobic():
                    self.residues_exposed_hydrophobic.append(res)
            except ValueError:
                print(f"Can't determine hydrophobicity of {res}: "
                      f"unknown amino acid.")

    def find_bounding_coord(self):
        """
        Find the extreme coordinates of the protein residues.

        Returns
        -------
        None.

        """
        x_min = float('inf')
        x_max = -float('inf')
        y_min = float('inf')
        y_max = -float('inf')
        z_min = float('inf')
        z_max = -float('inf')
        for res in [*self.residues_exposed, *self.residues_burrowed]:
            if res.coord.x < x_min:
                x_min = res.coord.x
            if res.coord.x > x_max:
                x_max = res.coord.x
            if res.coord.y < y_min:
                y_min = res.coord.y
            if res.coord.y > y_max:
                y_max = res.coord.y
            if res.coord.z < z_min:
                z_min = res.coord.z
            if res.coord.z > z_max:
                z_max = res.coord.z
        return x_min, x_max, y_min, y_max, z_min, z_max

    def add_membrane(self, sli):
        """
        Add the slice (i.e. membrane) position to the Protein structure.

        The membrane is represented by 2 residues, one for each of its
        borders. The residues are made of dummy atoms that build 2
        parallel grids.

        Parameters
        ----------
        sli : Slice
            The Slice to add to the Protein.

        Returns
        -------
        None.

        """
        smc = self.structure[self.model][self.chain]
        ids = [d.get_id()[1] for d in smc]
        bary = Point(*smc.center_of_mass())

        # Adding 2 dummy residues to represent the membrane delimiting planes.
        #last_id = smc[self.res_ids_pdb[-1]].id
        last_id = smc[ids[-1]].id
        mem1_id = (last_id[0], last_id[1]+1, last_id[2])
        mem2_id = (last_id[0], last_id[1]+2, last_id[2])
        mem1 = Bio.PDB.Residue.Residue(mem1_id, 'MEM', '')
        mem2 = Bio.PDB.Residue.Residue(mem2_id, 'MEM', '')
        smc.add(mem1)
        smc.add(mem2)

        # Creating grids to place dummy atoms in order to represent the
        # membrane 2 delimiting planes.
        resolution = 1
        shift = sli.center
        thickness = sli.thickness
        a = sli.normal.end.x
        b = sli.normal.end.y
        c = sli.normal.end.z
        # Finding bounding coordinates of the protein to know approximately
        # where to place the grids.
        x_min, x_max, y_min, y_max, z_min, z_max = self.find_bounding_coord()
        # Building the grids.
        xx, yy = np.mgrid[x_min:x_max:resolution, y_min:y_max:resolution]
        zz1 = (-a*xx - b*yy - thickness[0] + shift) / c
        zz2 = (-a*xx - b*yy + thickness[1] + shift) / c
        # Translation of the membrane planes to account for the centering
        # of the 3D space onto the protein barycenter.
        xx = xx + bary.x
        yy = yy + bary.y
        zz1 = zz1 + bary.z
        zz2 = zz2 + bary.z

        # Adding the dummy atoms to the 'membrane' residues.
        cpt = 1
        with warnings.catch_warnings():
            # If not ignore, will generate a warning for each atom because
            # its element is unknown (None by default).
            warnings.simplefilter('ignore', PDBConstructionWarning)
            for x, y, z in zip(xx.flatten(), yy.flatten(), zz1.flatten()):
                new = Bio.PDB.Atom.Atom(f'D{cpt}', np.array([x, y, z]),
                                            0, 1, 32, f' D{cpt} ', cpt)
                mem1.add(new)
                cpt += 1
        cpt = 1
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', PDBConstructionWarning)
            for x, y, z in zip(xx.flatten(), yy.flatten(), zz2.flatten()):
                new = Bio.PDB.Atom.Atom(f'D{cpt}', np.array([x, y, z]),
                                            0, 1, 32, f' D{cpt} ', cpt)
                mem2.add(new)
                cpt += 1

    def save_pdb(self, pdb_file):
        """
        Save the Protein in a PDB file.

        Parameters
        ----------
        pdb_file : str
            Absolute path of the output PDB file.

        Returns
        -------
        None.

        """
        # It's not possible to extract something from another model than 0.
        # TODO: derivate Bio.PDB.Dice.ChainSelector to implement model
        # choice support.
        smc = self.structure[self.model][self.chain]
        ids = [d.get_id()[1] for d in smc]
        Dice.extract(self.structure, self.chain, ids[0], ids[-1], pdb_file)

    def move(self, shift):
        """
        Move the Protein's residues.

        Parameters
        ----------
        shift : Point
            How much to move on x, y and z axis.

        Returns
        -------
        None.

        """
        for res in self.residues_exposed:
            res.coord += shift
        for res in self.residues_burrowed:
            res.coord += shift


class Slice():
    """
    Represent a potential membrane position.

    It is defined by 2 parallel plans.

    Parameters
    ----------
    protein : Protein
        Protein to which the Slice belong.
    center : float
        Position of the slice on the normal vector.
    normal : Vector
        Vector normal to the slice. Gives the axis for thickening the slice.
    method : {'ASA', 'simple'}, optional
        Method for computing the score representing the likelihood of the
        slice being the real membrane position. The default is 'ASA'.

    Attributes
    ----------
    protein : Protein
        Protein to which the Slice belong.
    center : float
        Position of the slice on the normal vector.
    normal : Vector
        Vector normal to the slice. Gives the axis for thickening the slice.
    score_method : {'ASA', 'simple'}
        Method for computing the score representing the likelihood of the
        slice being the real membrane position.
    thickness : [float, float]
        Thickness of the Slice, from the center to the normal vector
        starting point and ending point respectively.
    residues : list(Residue)
        Residues inside the Slice.
    score : float
        Score representing the likelihood of the slice being the real
        membrane position

    """
    def __init__(self, protein, center, normal, method='ASA'):
        self.protein = protein
        self.center = center
        self.normal = normal
        self.score_method = method
        self.thickness = [7, 7]
        self.residues = []
        self.score = 0
        n_res = self.find_residues()
        # If there's no residues in the slice, no need to update the score.
        if n_res != 0:
            try:
                self.compute_score(self.score_method)
            except ValueError:
                print("Method must be 'ASA' or 'simple'")

    def __repr__(self):
        thickness = sum(self.thickness)
        nb_residues = len(self.residues)
        return (f"(center: {self.center}, normal: {self.normal}, "
                f"thickness: {thickness}, nb_residues: {nb_residues}, "
                f"score: {self.score})")

    def __lt__(self, other):
        if self.score < other.score:
            return True
        else:
            return False

    def __gt__(self, other):
        if self.score > other.score:
            return True
        else:
            return False

    def __le__(self, other):
        if self.score <= other.score:
            return True
        else:
            return False

    def __ge__(self, other):
        if self.score >= other.score:
            return True
        else:
            return False

    def find_residues(self):
        """
        Find the exposed Residues that are inside the Slice.

        Returns
        -------
        int
            Number of exposed Residues inside the Slice.

        """
        self.residues = []
        for res in self.protein.residues_exposed:

            # Normal vector.
            a = self.normal.end.x
            b = self.normal.end.y
            c = self.normal.end.z

            # Plane vector.
            x = res.coord.x
            y = res.coord.y
            z = res.coord.z

            # Position of the planes along the normal vector.
            d1 = self.center - self.thickness[0]
            d2 = self.center + self.thickness[1]

            # The residues between the 2 planes are inside the Slice.
            if a*x + b*y + c*z >= d1 and a*x + b*y + c*z <= d2:
                self.residues.append(res)

        return len(self.residues)

    def compute_score(self, method='simple'):
        """
        Compute the membrane score of the Slice.

        The higher the score the more probable it is that the Slice
        represents the position of a membrane.
        'ASA' computes the ratio ASA of exposed hydrophobic residues in the
        slice to ASA of exposed hydrophobic residues in the protein.
        'simple' computes the ratio number of exposed hydrophobic residues
        in the slice to number of exposed hydrophobic residues in the protein.

        Parameters
        ----------
        method : {'ASA', 'simple'}, optional
            The method used to compute the Slice score. The default is
            'simple'.

        Raises
        ------
        ValueError
            Raised when the method to use is neither 'ASA' nor 'simple'.

        Returns
        -------
        None.

        """
        if method != 'ASA' and method != 'simple':
            raise ValueError

        if method == 'ASA':
            asa_slice = 0
            asa_total = 0

            for res in self.residues:
                try:
                    if res.is_hydrophobic():
                        asa_slice += res.asa
                    else:
                        asa_slice -= 0.5*res.asa
                except ValueError:
                    print(f"Can't determine hydrophobicity of {res}: "
                          f"unknown amino acid.")

            for res in self.protein.residues_exposed_hydrophobic:
                asa_total += res.asa
            self.score = asa_slice / asa_total

        elif method == 'simple':
            cpt_slice = 0

            for res in self.residues:
                try:
                    if res.is_hydrophobic():
                        cpt_slice += 1
                    else:
                        cpt_slice -= 0.5
                except ValueError:
                    print(f"Can't determine hydrophobicity of {res}: "
                          f"unknown amino acid.")
            cpt_total = 0

            for res in self.protein.residues_exposed_hydrophobic:
                cpt_total += 1
            self.score = cpt_slice / cpt_total

    def thicken(self, increment=1, normal_direction=True):
        """
        Thicken the Slice along the direction of the normal vector.

        Parameters
        ----------
        increment : float, optional
            How much to thicken the Slice. The default is 1.
        normal_direction : bool, optional
            In which direction to thicken the Slice. The default is True.
            True corresponds to the normal vector direction, False to the
            opposite direction.

        Returns
        -------
        None.

        """
        if normal_direction:
            self.thickness[1] += increment
        else:
            self.thickness[0] += increment

        n_res = self.find_residues()
        if n_res != 0:
            try:
                self.compute_score(self.score_method)
            except ValueError:
                print("Method must be 'ASA' or 'simple'")
        else:
            self.score = 0

    def maximise_score(self):
        """
        Thicken the Slice in order to maximise its score.

        Returns
        -------
        None.

        """
        base_score = self.score
        increment = 1

        # Exploring thickened slices toward the end of the normal vector.
        new_scores_up = [base_score]
        self.thicken(increment, normal_direction=True)
        cpt = 0
        while self.score != 0:
            new_scores_up.append(self.score)
            self.thicken(increment, normal_direction=True)
            cpt += 1
            if cpt >= 5 and new_scores_up[-5:].count(new_scores_up[-1]) == 5:
                # The search stops when there 5 consecutive identical scores.
                break
        # Setting the thickness to the one that yields the maximal score.
        best_index = np.argmax(new_scores_up)
        backtrack_steps = len(new_scores_up[best_index:])
        # Thinning the slice to backtrack to the best one.
        self.thicken(-increment * backtrack_steps, normal_direction=True)

        # Same but toward the start of the normal vector.
        new_scores_down = [base_score]
        self.thicken(increment, normal_direction=False)
        cpt = 0
        while self.score != 0:
            new_scores_down.append(self.score)
            self.thicken(increment, normal_direction=False)
            cpt += 1
            if (cpt >= 5
                and new_scores_down[-5:].count(new_scores_down[-1])) == 5:
                break
        best_index = np.argmax(new_scores_down)
        backtrack_steps = len(new_scores_down[best_index:])
        self.thicken(-increment * backtrack_steps, normal_direction=False)
