"""Contains the classes that deal with the different dynamics required in
different types of ensembles.

Holds the algorithms required for normal mode propagators, and the objects to
do the constant temperature and pressure algorithms. Also calculates the
appropriate conserved energy quantity for the ensemble of choice.
"""

# This file is part of i-PI.
# i-PI Copyright (C) 2014-2015 i-PI developers
# See the "licenses" directory for full license information.


import numpy as np

from ipi.utils.messages import warning
from ipi.utils.depend import dd
from ipi.utils.units import Constants
from ipi.engine.thermostats import *
from ipi.engine.barostats import *
from ipi.engine.motion.alchemy import *
from ipi.engine.forces import Forces, ScaledForceComponent
from ipi.engine.eda import EDA

__all__ = ["Ensemble", "ensemble_swap"]

# IMPORTANT - THIS MUST BE KEPT UP-TO-DATE WHEN THE ENSEMBLE CLASS IS CHANGED


def ensemble_swap(ens1, ens2):
    """Swaps the definitions of the two ensembles, by
    exchanging all of the inner properties."""

    if ens1.temp != ens2.temp:
        ens1.temp, ens2.temp = ens2.temp, ens1.temp
    if ens1.pext != ens2.pext:
        ens1.pext, ens2.pext = ens2.pext, ens1.pext
    if np.linalg.norm(ens1.stressext - ens2.stressext) > 1e-10:
        tmp = dstrip(ens1.stressext).copy()
        ens1.stressext[:] = ens2.stressext
        ens2.stressext[:] = tmp
    if len(ens1.bweights) != len(ens2.bweights):
        raise ValueError(
            "Cannot exchange ensembles that have different numbers of bias components"
        )
    if len(ens1.hweights) != len(ens2.hweights):
        raise ValueError(
            "Cannot exchange ensembles that are described by different forces"
        )
    if not np.array_equal(ens1.bweights, ens2.bweights):
        ens1.bweights, ens2.bweights = (
            dstrip(ens2.bweights).copy(),
            dstrip(ens1.bweights).copy(),
        )
    if not np.array_equal(ens1.hweights, ens2.hweights):
        ens1.hweights, ens2.hweights = (
            dstrip(ens2.hweights).copy(),
            dstrip(ens1.hweights).copy(),
        )


class Ensemble(dobject):

    """Base ensemble class.

    Defines the thermodynamic state of the system.

    Depend objects:
        temp: The system's temperature.
        pext: The systems's pressure
        stressext: The system's stress tensor
        bias: Explicit bias forces
    """

    def __init__(
        self,
        eens=0.0,
        econs=0.0,
        temp=None,
        pext=None,
        stressext=None,
        bcomponents=None,
        bweights=None,
        hweights=None,
        time=0.0,
        # amp=None,
        # freq=None,
        # phase=None,
        # peak=None,
        # sigma=None,
        # bec=None,
        # cdip=True,
        # tacc=0.0,
        # cbec=False,
    ):
        """Initialises Ensemble.

        Args:
            temp: The temperature.
            fixcom: An optional boolean which decides whether the centre of mass
                motion will be constrained or not. Defaults to False.
        """
        dself = dd(self)

        dself.temp = depend_value(name="temp")
        if temp is not None:
            self.temp = temp
        else:
            self.temp = -1.0

        dself.stressext = depend_array(name="stressext", value=np.zeros((3, 3), float))
        if stressext is not None:
            self.stressext = np.reshape(np.asarray(stressext), (3, 3))
        else:
            self.stressext = -1.0

        dself.pext = depend_value(name="pext")
        if pext is not None:
            self.pext = pext
        else:
            self.pext = -1.0

        dself.eens = depend_value(name="eens")
        if eens is not None:
            self.eens = eens
        else:
            self.eens = 0.0

        # the bias force contains two bits: explicit biases (that are meant to represent non-physical external biasing potentials)
        # and hamiltonian weights (that will act by scaling different physical components of the force). Both are bound as components
        # of the "bias force" evaluator, but their meaning (and the wiring further down in bind()) differ.

        # these are the additional bias components
        if bcomponents is None:
            bcomponents = []
        self.bcomp = bcomponents
        self.bias = Forces()

        # and their weights
        if bweights is None or len(bweights) == 0:
            bweights = np.ones(len(self.bcomp))

        dself.bweights = depend_array(name="bweights", value=np.asarray(bweights))

        # weights of the Hamiltonian scaling
        if hweights is None:
            hweights = np.ones(0)
        self.hweights = np.asarray(hweights)

        # ES

        # if peak is not None and peak < 0:
        #     raise ValueError(
        #         "peak < 0: the peak of the external electric field can only be positive"
        #     )
        # if sigma is not None and sigma < 0:
        #     raise ValueError(
        #         "sigma < 0: the standard deviation of the gaussian envelope function of the external electric field has to be positive"
        #     )

        # Internal time counter
        dself.time = depend_value(name="time", value=time)

        #
        # dself.amp = depend_array(
        #     name="amp", value=amp if amp is not None else np.zeros(3)
        # )
        # dself.freq = depend_value(
        #     name="freq", value=freq if freq is not None else 0.0
        # )
        # dself.phase = depend_value(
        #     name="phase", value=phase if phase is not None else 0.0
        # )
        # dself.peak = depend_value(
        #     name="peak", value=peak if peak is not None else 0.0
        # )
        # dself.sigma = depend_value(
        #     name="sigma", value=sigma if sigma is not None else np.inf
        # )
        # dself.bec = depend_array(
        #     name="bec", value=bec if bec is not None else np.zeros(0)
        # )
        # dself.cbec = depend_array(name="cbec", value=cbec)
        # dself.cdip = depend_array(name="cdip", value=cdip)
        # dself.tacc   = depend_array(name="tacc"   ,value=tacc)

        # self.eda = EDA(amp, freq, phase, peak, sigma, cbec, bec) # cdip
        # try :
        #     self.eda = EDA(amp,freq,phase,peak,sigma,cdip,cbec,bec)
        # except :
        #     print("WARNING: 'EDA' object not instantiated")

    def copy(self):
        return Ensemble(
            eens=self.eens,
            econs=0.0,
            temp=self.temp,
            pext=self.pext,
            stressext=dstrip(self.stressext).copy(),
            bcomponents=self.bcomp,
            bweights=dstrip(self.bweights).copy(),
            hweights=dstrip(self.hweights).copy(),
            time=self.time,
            # amp=self.amp,
            # freq=self.freq,
            # phase=self.phase,
            # peak=self.peak,
            # sigma=self.sigma,
            # bec=self.bec,
            # cdip=self.cdip,
            # tacc=self.tacc,
            # cBEC=self.cBEC,
        )

    def bind(
        self,
        beads,
        nm,
        cell,
        bforce,
        fflist,
        output_maker,
        elist=[],
        xlpot=[],
        xlkin=[],
    ):
        self.beads = beads
        self.cell = cell
        self.forces = bforce
        self.nm = nm
        dself = dd(self)
        self.output_maker = output_maker

        # this binds just the explicit bias forces
        self.bias.bind(
            self.beads,
            self.cell,
            self.bcomp,
            fflist,
            open_paths=nm.open_paths,
            output_maker=self.output_maker,
        )

        dself.econs = depend_value(name="econs", func=self.get_econs)
        # dependencies of the conserved quantity
        dself.econs.add_dependency(dd(self.nm).kin)
        dself.econs.add_dependency(dd(self.forces).pot)
        dself.econs.add_dependency(dd(self.bias).pot)
        dself.econs.add_dependency(dd(self.nm).vspring)
        dself.econs.add_dependency(dself.eens)

        # pipes the weights to the list of weight vectors
        i = 0
        for fc in self.bias.mforces:
            if fc.weight != 1:
                warning(
                    "The weight given to forces used in an ensemble bias are given a weight determined by bias_weight"
                )
            dpipe(dself.bweights, dd(fc).weight, i)
            i += 1

        # add Hamiltonian REM bias components
        if len(self.hweights) == 0:
            self.hweights = np.ones(len(self.forces.mforces))

        dself.hweights = depend_array(name="hweights", value=np.asarray(self.hweights))

        # we use ScaledForceComponents to replicate the physical forces without (hopefully) them being actually recomputed
        for ic in range(len(self.forces.mforces)):
            sfc = ScaledForceComponent(self.forces.mforces[ic], 1.0)
            self.bias.add_component(self.forces.mbeads[ic], self.forces.mrpc[ic], sfc)
            dd(sfc).scaling._func = lambda i=ic: self.hweights[i] - 1
            dd(sfc).scaling.add_dependency(dself.hweights)

        self._elist = []

        for e in elist:
            self.add_econs(e)

        dself.lpens = depend_value(
            name="lpens", func=self.get_lpens, dependencies=[dself.temp]
        )
        dself.lpens.add_dependency(dd(self.nm).kin)
        dself.lpens.add_dependency(dd(self.forces).pot)
        dself.lpens.add_dependency(dd(self.bias).pot)
        dself.lpens.add_dependency(dd(self.nm).vspring)

        # extended Lagrangian terms for the ensemble
        self._xlpot = []
        for p in xlpot:
            self.add_xlpot(p)

        self._xlkin = []
        for k in xlkin:
            self.add_xlkin(k)


    def add_econs(self, e):
        self._elist.append(e)
        dd(self).econs.add_dependency(e)

    def add_xlpot(self, p):
        self._xlpot.append(p)
        dd(self).lpens.add_dependency(p)

    def add_xlkin(self, k):
        self._xlkin.append(k)
        dd(self).lpens.add_dependency(k)

    def get_econs(self):
        """Calculates the conserved energy quantity for constant energy
        ensembles.
        """

        eham = self.nm.vspring + self.nm.kin + self.forces.pot

        eham += self.bias.pot  # bias

        for e in self._elist:
            eham += e.get()

        return eham + self.eens

    def get_lpens(self):
        """Returns the ensemble probability (modulo the partition function)
        for the ensemble.
        """

        lpens = self.forces.pot + self.bias.pot + self.nm.kin + self.nm.vspring

        # inlcude terms associated with an extended Lagrangian integrator of some sort
        for p in self._xlpot:
            lpens += p.get()
        for k in self._xlkin:
            lpens += k.get()

        lpens *= -1.0 / (Constants.kb * self.temp * self.beads.nbeads)
        return lpens
