# Copyright 2016, FBPIC contributors
# Authors: Remi Lehe, Manuel Kirchen
# License: 3-Clause-BSD-LBNL
"""
This file is part of the Fourier-Bessel Particle-In-Cell code (FB-PIC)
It defines numba methods that are used in particle ionization.

Apart from synthactic, this file is very close to cuda_methods.py
"""
import numba
from scipy.constants import c, e
from .inline_functions import get_ionization_probability_numba, \
    get_E_amplitude_numba, copy_ionized_electrons_batch_numba

@numba.jit()
def ionize_ions_numba( N_batch, batch_size, Ntot, z_max,
    n_ionized, is_ionized, ionization_level, random_draw,
    adk_prefactor, adk_power, adk_exp_prefactor,
    ux, uy, uz, Ex, Ey, Ez, Bx, By, Bz, w, neutral_weight ):
    """
    # TODO
    """
    # Loop over batches of particles
    for i_batch in range( N_batch ):

        # Set the count of ionized particles in the batch to 0
        n_ionized[i_batch] = 0

        # Loop through the batch
        N_max = min( (i_batch+1)*batch_size, Ntot )
        for ip in range( i_batch*batch_size, N_max ):

            # Skip the ionization routine, if the maximal ionization level
            # has already been reached for this macroparticle
            level = ionization_level[ip]
            if level >= z_max:
                continue

            # Calculate the amplitude of the electric field,
            # in the frame of the electrons (device inline function)
            E = get_E_amplitude_numba( ux[ip], uy[ip], uz[ip],
                    Ex[ip], Ey[ip], Ez[ip], c*Bx[ip], c*By[ip], c*Bz[ip] )
            # Get ADK rate (device inline function)
            p = get_ionization_probability_numba( E, adk_prefactor[level],
                adk_power[level], adk_exp_prefactor[level] )
            # Ionize particles
            if random_draw[ip] < p:
                # Set the corresponding flag and update particle count
                is_ionized[ip] = 1
                n_ionized[i_batch] += 1
                # Update the ionization level and the corresponding weight
                ionization_level[ip] += 1
                w[ip] = e * ionization_level[ip] * neutral_weight[ip]
            else:
                is_ionized[ip] = 0

@numba.jit()
def copy_ionized_electrons_numba(
    N_batch, batch_size, elec_old_Ntot, ion_Ntot,
    n_ionized, is_ionized,
    elec_x, elec_y, elec_z, elec_inv_gamma,
    elec_ux, elec_uy, elec_uz, elec_w,
    ion_x, ion_y, ion_z, ion_inv_gamma,
    ion_ux, ion_uy, ion_uz, ion_neutral_weight ):
    """
    # TODO
    """
    # Select the current batch
    for i_batch in range( N_batch ):
        copy_ionized_electrons_batch_numba(
            i_batch, batch_size, elec_old_Ntot, ion_Ntot,
            n_ionized, is_ionized,
            elec_x, elec_y, elec_z, elec_inv_gamma,
            elec_ux, elec_uy, elec_uz, elec_w,
            ion_x, ion_y, ion_z, ion_inv_gamma,
            ion_ux, ion_uy, ion_uz, ion_neutral_weight )