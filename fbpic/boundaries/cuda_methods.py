# Copyright 2016, FBPIC contributors
# Authors: Remi Lehe, Manuel Kirchen
# License: 3-Clause-BSD-LBNL
"""
This file is part of the Fourier-Bessel Particle-In-Cell code (FB-PIC)
It defines a set of generic functions that operate on a GPU.
"""
from numba import cuda

@cuda.jit
def copy_vec_to_gpu_buffer( vec_buffer_l, vec_buffer_r,
                            grid_0_r, grid_0_t, grid_0_z,
                            grid_1_r, grid_1_t, grid_1_z,
                            copy_left, copy_right, nz_start, nz_end ):
    """
    Copy the ng inner domain cells of grid_0_r, ..., grid_1_z
    to the GPU buffer vec_buffer_l and vec_buffer_r.

    Parameters
    ----------
    vec_buffer_l, vec_buffer_r: ndarrays of complexs (device arrays)
        Arrays of shape (6, nz_end-nz_start, Nr), which serve as buffer
        for transmission to CPU, and then sending via MPI. They hold the
        values of a vector field in either the ng inner cells of the domain
        or the ng outer + ng inner cells of the domain, to the left and right.

    grid_m_x: ndarrays of complexs (device arrays)
        Arrays of shape (Nz, Nr), which contain the different component
        of the vector field (r, t, z), in the modes 0 and 1.
        (m = mode, x = coordinate)

    copy_left, copy_right: bool
        Whether to copy the buffers to the left and right of the local domain
        (Buffers are not copied at the left end and right end of the
        global simulation box.)

    nz_start: int
        The start index in z, of the cell region which is copied to the
        buffers. The start is defined as an offset from the most outer cell
        on either the left or the right side of the enlarged domain.

    nz_end: int
        The end index in z, of the cell region which is copied to the
        buffers. The end is defined as an offset from the most outer cell
        on either the left or the right side of the enlarged domain.
    """
    # Dimension of the arrays
    Nz, Nr = grid_0_r.shape

    # Obtain Cuda grid
    iz, ir = cuda.grid(2)

    # Copy the inner regions of the domain to the buffer
    if ir < Nr:
        if iz < (nz_end - nz_start):
            # At the left end
            if copy_left:
                iz_left = nz_start + iz
                vec_buffer_l[0, iz, ir] = grid_0_r[ iz_left, ir ]
                vec_buffer_l[1, iz, ir] = grid_0_t[ iz_left, ir ]
                vec_buffer_l[2, iz, ir] = grid_0_z[ iz_left, ir ]
                vec_buffer_l[3, iz, ir] = grid_1_r[ iz_left, ir ]
                vec_buffer_l[4, iz, ir] = grid_1_t[ iz_left, ir ]
                vec_buffer_l[5, iz, ir] = grid_1_z[ iz_left, ir ]
            # At the right end
            if copy_right:
                iz_right = Nz - nz_end + iz
                vec_buffer_r[0, iz, ir] = grid_0_r[ iz_right, ir ]
                vec_buffer_r[1, iz, ir] = grid_0_t[ iz_right, ir ]
                vec_buffer_r[2, iz, ir] = grid_0_z[ iz_right, ir ]
                vec_buffer_r[3, iz, ir] = grid_1_r[ iz_right, ir ]
                vec_buffer_r[4, iz, ir] = grid_1_t[ iz_right, ir ]
                vec_buffer_r[5, iz, ir] = grid_1_z[ iz_right, ir ]

@cuda.jit
def copy_scal_to_gpu_buffer( scal_buffer_l, scal_buffer_r,
                             grid_0, grid_1,
                             copy_left, copy_right, nz_start, nz_end ):
    """
    Copy the ng inner domain cells of grid_0, ..., grid_1
    to the GPU buffer scal_buffer_l and scal_buffer_r.

    Parameters
    ----------
    scal_buffer_l, scal_buffer_r: ndarrays of complexs (device arrays)
        Arrays of shape (2, nz_end-nz_start, Nr), which serve as buffer
        for transmission to CPU, and then sending via MPI. They hold the
        values of a scalar field in either the ng inner cells of the domain
        or the ng outer + ng inner cells of the domain, to the left and right.

    grid_m: ndarrays of complexs (device arrays)
        Arrays of shape (Nz, Nr), which contain the different modes 0 and 1
        of the scalar field.
        (m = mode)

    copy_left, copy_right: bool
        Whether to copy the buffers to the left and right of the local domain
        (Buffers are not copied at the left end and right end of the
        global simulation box.)

    nz_start: int
        The start index in z, of the cell region which is copied to the
        buffers. The start is defined as an offset from the most outer cell
        on either the left or the right side of the enlarged domain.

    nz_end: int
        The end index in z, of the cell region which is copied to the
        buffers. The end is defined as an offset from the most outer cell
        on either the left or the right side of the enlarged domain.
    """
    # Dimension of the arrays
    Nz, Nr = grid_0.shape

    # Obtain Cuda grid
    iz, ir = cuda.grid(2)

    # Copy the inner regions of the domain to the buffer
    if ir < Nr:
        if iz < (nz_end - nz_start):
            # At the left end
            if copy_left:
                iz_left = nz_start + iz
                scal_buffer_l[0, iz, ir] = grid_0[ iz_left, ir ]
                scal_buffer_l[1, iz, ir] = grid_1[ iz_left, ir ]
            # At the right end
            if copy_right:
                iz_right = Nz - nz_end + iz
                scal_buffer_r[0, iz, ir] = grid_0[ iz_right, ir ]
                scal_buffer_r[1, iz, ir] = grid_1[ iz_right, ir ]

@cuda.jit
def replace_vec_from_gpu_buffer( vec_buffer_l, vec_buffer_r,
                                 grid_0_r, grid_0_t, grid_0_z,
                                 grid_1_r, grid_1_t, grid_1_z,
                                 copy_left, copy_right, nz_start, nz_end ):
    """
    Replace a region (guard region) of grid_0_r, ..., grid_1_z
    by the GPU buffer vec_buffer_l and vec_buffer_r.

    Parameters
    ----------
    vec_buffer_l, vec_buffer_r: ndarrays of complexs (device arrays)
        Arrays of shape (6, nz_end-nz_start, Nr), which are the buffers
        sent via MPI and received by the CPU.

    grid_m_x: ndarrays of complexs (device arrays)
        Arrays of shape (Nz, Nr), which contain the different component
        of the vector field (r, t, z), in the modes 0 and 1.
        (m = mode, x = coordinate)

    copy_left, copy_right: bool
        Whether to copy the buffers to the left and right of the local domain
        (Buffers are not copied at the left end and right end of the
        global simulation box.)

    nz_start: int
        The start index in z, of the cell region which is copied to the
        buffers. The start is defined as an offset from the most outer cell
        on either the left or the right side of the enlarged domain.

    nz_end: int
        The end index in z, of the cell region which is copied to the
        buffers. The end is defined as an offset from the most outer cell
        on either the left or the right side of the enlarged domain.
    """
    # Dimension of the arrays
    Nz, Nr = grid_0_r.shape

    # Obtain Cuda grid
    iz, ir = cuda.grid(2)

    # Copy the inner regions of the domain to the buffer
    if ir < Nr:
        if iz < (nz_end - nz_start):
            # At the left end
            if copy_left:
                iz_left = iz
                grid_0_r[ iz_left, ir ] = vec_buffer_l[0, iz, ir]
                grid_0_t[ iz_left, ir ] = vec_buffer_l[1, iz, ir]
                grid_0_z[ iz_left, ir ] = vec_buffer_l[2, iz, ir]
                grid_1_r[ iz_left, ir ] = vec_buffer_l[3, iz, ir]
                grid_1_t[ iz_left, ir ] = vec_buffer_l[4, iz, ir]
                grid_1_z[ iz_left, ir ] = vec_buffer_l[5, iz, ir]
            # At the right end
            if copy_right:
                iz_right = Nz - (nz_end - nz_start) + iz
                grid_0_r[ iz_right, ir ] = vec_buffer_r[0, iz, ir]
                grid_0_t[ iz_right, ir ] = vec_buffer_r[1, iz, ir]
                grid_0_z[ iz_right, ir ] = vec_buffer_r[2, iz, ir]
                grid_1_r[ iz_right, ir ] = vec_buffer_r[3, iz, ir]
                grid_1_t[ iz_right, ir ] = vec_buffer_r[4, iz, ir]
                grid_1_z[ iz_right, ir ] = vec_buffer_r[5, iz, ir]

@cuda.jit
def replace_scal_from_gpu_buffer( scal_buffer_l, scal_buffer_r,
                                 grid_0, grid_1,
                                 copy_left, copy_right, nz_start, nz_end ):
    """
    Replace a region (guard region) of grid_0, ..., grid_1
    by the GPU buffer scal_buffer_l and scal_buffer_r.

    Parameters
    ----------
    scal_buffer_l, scal_buffer_r: ndarrays of complexs (device arrays)
        Arrays of shape (2, nz_end-nz_start, Nr), which are the buffers
        sent via MPI and received by the CPU.

    grid_m: ndarrays of complexs (device arrays)
        Arrays of shape (Nz, Nr), which contain the different modes 0 and 1
        of the scalar field.
        (m = mode)

    copy_left, copy_right: bool
        Whether to copy the buffers to the left and right of the local domain
        (Buffers are not copied at the left end and right end of the
        global simulation box.)

    nz_start: int
        The start index in z, of the cell region which is copied to the
        buffers. The start is defined as an offset from the most outer cell
        on either the left or the right side of the enlarged domain.

    nz_end: int
        The end index in z, of the cell region which is copied to the
        buffers. The end is defined as an offset from the most outer cell
        on either the left or the right side of the enlarged domain.
    """
    # Dimension of the arrays
    Nz, Nr = grid_0.shape

    # Obtain Cuda grid
    iz, ir = cuda.grid(2)

    # Copy the inner regions of the domain to the buffer
    if ir < Nr:
        if iz < (nz_end - nz_start):
            # At the left end
            if copy_left:
                iz_left = iz
                grid_0[ iz_left, ir ] = scal_buffer_l[0, iz, ir]
                grid_1[ iz_left, ir ] = scal_buffer_l[1, iz, ir]
            # At the right end
            if copy_right:
                iz_right = Nz - (nz_end - nz_start) + iz
                grid_0[ iz_right, ir ] = scal_buffer_r[0, iz, ir]
                grid_1[ iz_right, ir ] = scal_buffer_r[1, iz, ir]


@cuda.jit
def add_vec_from_gpu_buffer( vec_buffer_l, vec_buffer_r,
                             grid_0_r, grid_0_t, grid_0_z,
                             grid_1_r, grid_1_t, grid_1_z,
                             copy_left, copy_right, nz_start, nz_end ):
    """
    Add the the GPU buffer vec_buffer_l and vec_buffer_r
    to the vector field grids, grid_0_r, ..., grid_1_z.

    Parameters
    ----------
    vec_buffer_l, vec_buffer_r: ndarrays of complexs (device arrays)
        Arrays of shape (6, nz_end-nz_start, Nr), which are the buffers
        sent via MPI and received by the CPU.

    grid_m_x: ndarrays of complexs (device arrays)
        Arrays of shape (Nz, Nr), which contain the different component
        of the vector field (r, t, z), in the modes 0 and 1.
        (m = mode, x = coordinate)

    copy_left, copy_right: bool
        Whether to copy the buffers to the left and right of the local domain
        (Buffers are not copied at the left end and right end of the
        global simulation box.)

    nz_start: int
        The start index in z, of the cell region which is copied to the
        buffers. The start is defined as an offset from the most outer cell
        on either the left or the right side of the enlarged domain.

    nz_end: int
        The end index in z, of the cell region which is copied to the
        buffers. The end is defined as an offset from the most outer cell
        on either the left or the right side of the enlarged domain.
    """
    # Dimension of the arrays
    Nz, Nr = grid_0_r.shape

    # Obtain Cuda grid
    iz, ir = cuda.grid(2)

    # Copy the inner regions of the domain to the buffer
    if ir < Nr:
        if iz < (nz_end - nz_start):
            # At the left end
            if copy_left:
                iz_left = iz
                grid_0_r[ iz_left, ir ] += vec_buffer_l[0, iz, ir]
                grid_0_t[ iz_left, ir ] += vec_buffer_l[1, iz, ir]
                grid_0_z[ iz_left, ir ] += vec_buffer_l[2, iz, ir]
                grid_1_r[ iz_left, ir ] += vec_buffer_l[3, iz, ir]
                grid_1_t[ iz_left, ir ] += vec_buffer_l[4, iz, ir]
                grid_1_z[ iz_left, ir ] += vec_buffer_l[5, iz, ir]
            # At the right end
            if copy_right:
                iz_right = Nz - (nz_end - nz_start) + iz
                grid_0_r[ iz_right, ir ] += vec_buffer_r[0, iz, ir]
                grid_0_t[ iz_right, ir ] += vec_buffer_r[1, iz, ir]
                grid_0_z[ iz_right, ir ] += vec_buffer_r[2, iz, ir]
                grid_1_r[ iz_right, ir ] += vec_buffer_r[3, iz, ir]
                grid_1_t[ iz_right, ir ] += vec_buffer_r[4, iz, ir]
                grid_1_z[ iz_right, ir ] += vec_buffer_r[5, iz, ir]

@cuda.jit
def add_scal_from_gpu_buffer( scal_buffer_l, scal_buffer_r,
                              grid_0, grid_1,
                              copy_left, copy_right, nz_start, nz_end ):
    """
    Add the the GPU buffer scal_buffer_l and scal_buffer_r
    to the scalar field grids, grid_0_r, ..., grid_1_z.

    Parameters
    ----------
    scal_buffer_l, scal_buffer_r: ndarrays of complexs (device arrays)
        Arrays of shape (2, nz_end-nz_start, Nr), which are the buffers
        sent via MPI and received by the CPU.

    grid_m: ndarrays of complexs (device arrays)
        Arrays of shape (Nz, Nr), which contain the different modes 0 and 1
        of the scalar field.
        (m = mode)

    copy_left, copy_right: bool
        Whether to copy the buffers to the left and right of the local domain
        (Buffers are not copied at the left end and right end of the
        global simulation box.)

    nz_start: int
        The start index in z, of the cell region which is copied to the
        buffers. The start is defined as an offset from the most outer cell
        on either the left or the right side of the enlarged domain.

    nz_end: int
        The end index in z, of the cell region which is copied to the
        buffers. The end is defined as an offset from the most outer cell
        on either the left or the right side of the enlarged domain.
    """
    # Dimension of the arrays
    Nz, Nr = grid_0.shape

    # Obtain Cuda grid
    iz, ir = cuda.grid(2)

    # Copy the inner regions of the domain to the buffer
    if ir < Nr:
        if iz < (nz_end - nz_start):
            # At the left end
            if copy_left:
                iz_left = iz
                grid_0[ iz_left, ir ] += scal_buffer_l[0, iz, ir]
                grid_1[ iz_left, ir ] += scal_buffer_l[1, iz, ir]
            # At the right end
            if copy_right:
                iz_right = Nz - (nz_end - nz_start) + iz
                grid_0[ iz_right, ir ] += scal_buffer_r[0, iz, ir]
                grid_1[ iz_right, ir ] += scal_buffer_r[1, iz, ir]

# CUDA damping kernels:
# --------------------
@cuda.jit
def cuda_damp_EB_left( Er, Et, Ez, Br, Bt, Bz, damp_array, n_guard, n_damp ):
    """
    Multiply the E and B fields in the left guard cells
    by damp_array.

    Parameters :
    ------------
    Er, Et, Ez, Br, Bt, Bz: 2darrays of complexs
        Contain the fields to be damped
        The first axis corresponds to z and the second to r

    damp_array : 1darray of floats
        An array of length n_guard+n_damp,
        which contains the damping factors.

    n_guard: int
        Number of guard cells

    n_damp: int
        Number of damping cells
    """
    # Obtain Cuda grid
    iz, ir = cuda.grid(2)

    # Obtain the size of the array along z and r
    Nz, Nr = Er.shape

    # Modify the fields
    if ir < Nr :
        # Apply the damping arrays
        if iz < n_guard+n_damp:
            damp_factor_left = damp_array[iz]

            # At the left end
            Er[iz, ir] *= damp_factor_left
            Et[iz, ir] *= damp_factor_left
            Ez[iz, ir] *= damp_factor_left
            Br[iz, ir] *= damp_factor_left
            Bt[iz, ir] *= damp_factor_left
            Bz[iz, ir] *= damp_factor_left

@cuda.jit
def cuda_damp_EB_right( Er, Et, Ez, Br, Bt, Bz, damp_array, n_guard, n_damp ):
    """
    Multiply the E and B fields in the right guard cells
    by damp_array.

    Parameters :
    ------------
    Er, Et, Ez, Br, Bt, Bz : 2darrays of complexs
        Contain the fields to be damped
        The first axis corresponds to z and the second to r

    damp_array : 1darray of floats
        An array of length n_guard+n_damp,
        which contains the damping factors.

    n_guard: int
        Number of guard cells

    n_damp: int
        Number of damping cells
    """
    # Obtain Cuda grid
    iz, ir = cuda.grid(2)

    # Obtain the size of the array along z and r
    Nz, Nr = Er.shape

    # Modify the fields
    if ir < Nr :
        # Apply the damping arrays
        if iz < n_guard+n_damp:
            damp_factor_right = damp_array[iz]

            # At the right end
            iz_right = Nz - iz - 1
            Er[iz_right, ir] *= damp_factor_right
            Et[iz_right, ir] *= damp_factor_right
            Ez[iz_right, ir] *= damp_factor_right
            Br[iz_right, ir] *= damp_factor_right
            Bt[iz_right, ir] *= damp_factor_right
            Bz[iz_right, ir] *= damp_factor_right
