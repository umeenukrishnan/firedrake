import firedrake_configuration
import os
import sys
config = firedrake_configuration.get_config()
if "PETSC_DIR" in os.environ and not config["options"]["honour_petsc_dir"]:
    if os.environ["PETSC_DIR"] != os.path.join(sys.prefix, "src", "petsc")\
       or os.environ["PETSC_ARCH"] != "default":
        raise ImportError("PETSC_DIR is set, but you did not install with --honour-petsc-dir.\n"
                          "Please unset PETSC_DIR (and PETSC_ARCH) before using Firedrake.")
elif "PETSC_DIR" not in os.environ and config["options"]["honour_petsc_dir"]:
    raise ImportError("Firedrake was installed with --honour-petsc-dir, but PETSC_DIR is not set.\n"
                      "Please set PETSC_DIR (and PETSC_ARCH) before using Firedrake.")
elif not config["options"]["honour_petsc_dir"]:  # Using our own PETSC.
    os.environ["PETSC_DIR"] = os.path.join(sys.prefix, "src", "petsc")
    os.environ["PETSC_ARCH"] = "default"
del sys, config

# Ensure petsc is initialised by us before anything else gets in there.
import firedrake.petsc as petsc

# Initialise PETSc events for both import and entire duration of program
_is_logging = "log_view" in petsc.OptionsManager.commandline_options
if _is_logging:
    _main_event = petsc.PETSc.Log.Event("firedrake")
    _main_event.begin()

    _init_event = petsc.PETSc.Log.Event("firedrake.__init__")
    _init_event.begin()

    import atexit
    atexit.register(lambda: _main_event.end())
    del atexit
del petsc

# UFL Exprs come with a custom __del__ method, but we hold references
# to them /everywhere/, some of which are circular (the Mesh object
# holds a ufl.Domain that references the Mesh).  The Python2 GC
# explicitly DOES NOT collect such reference cycles (even though it
# can deal with normal cycles).  Quoth the documentation:
#
#     Objects that have __del__() methods and are part of a reference
#     cycle cause the entire reference cycle to be uncollectable,
#     including objects not necessarily in the cycle but reachable
#     only from it.
#
# To get around this, since the default __del__ on Expr is just
# "pass", we just remove the method from the definition of Expr.
import ufl
try:
    del ufl.core.expr.Expr.__del__
except AttributeError:
    pass
del ufl
from ufl import *
# Set up the cache directories before importing PyOP2.
firedrake_configuration.setup_cache_dirs()

# By default we disable pyadjoint annotation.
# To enable annotation, the user has to import firedrake_adjoint
import pyadjoint
pyadjoint.pause_annotation()
del pyadjoint

from firedrake_citations import Citations    # noqa: F401
# Always get the firedrake paper.
Citations().register("Rathgeber2016")
from pyop2 import op2                        # noqa: F401
from pyop2.mpi import COMM_WORLD, COMM_SELF  # noqa: F401

from firedrake.assemble import *
from firedrake.bcs import *
from firedrake.checkpointing import *
from firedrake.constant import *
from firedrake.exceptions import *
from firedrake.expression import *
from firedrake.function import *
from firedrake.functionspace import *
from firedrake.interpolation import *
from firedrake.output import *
from firedrake.linear_solver import *
from firedrake.preconditioners import *
from firedrake.mesh import *
from firedrake.mg.mesh import *
from firedrake.mg.interface import *
from firedrake.mg.embedded import *
from firedrake.mg.opencascade_mh import *
from firedrake.norms import *
from firedrake.nullspace import *
from firedrake.optimizer import *
from firedrake.parameters import *
from firedrake.parloops import *
from firedrake.plot import *
from firedrake.projection import *
from firedrake.slate import *
from firedrake.slope_limiter import *
from firedrake.solving import *
from firedrake.ufl_expr import *
from firedrake.utility_meshes import *
from firedrake.variational_solver import *
from firedrake.vector import *
from firedrake.version import __version__ as ver, __version_info__, check  # noqa: F401
from firedrake.ensemble import *
from firedrake.randomfunctiongen import *

from firedrake.logging import *
# Set default log level
set_log_level(WARNING)
set_log_handlers(comm=COMM_WORLD)

check()
del check

from firedrake._version import get_versions
__version__ = get_versions()['version']
del get_versions

# Try to detect threading and either disable or warn user
# Threading may come from
# - OMP_NUM_THREADS: openmp,
# - OPENBLAS_NUM_THREADS: openblas,
# - MKL_NUM_THREADS: mkl,
# - VECLIB_MAXIMUM_THREADS: accelerate,
# - NUMEXPR_NUM_THREADS: numexpr
# We only handle the first two cases
from ctypes import cdll
from ctypes.util import find_library
try:
    _openblas_lib = find_library('openblas')
    _openblas_dll = cdll.LoadLibrary(_openblas_lib)
    _openblas_dll.openblas_set_num_threads(1)
except (OSError, AttributeError):
    warning('Cannot set OpenBLAS threads, if you are using another BLAS'
            'implementation, be sure to limit the number of threads to 1')

# OMP_NUM_THREADS can be set to a comma-separated list of positive integers
try:
    _omp_num_threads = int(os.environ.get('OMP_NUM_THREADS'))
except (ValueError, TypeError):
    _omp_num_threads = None
if (_omp_num_threads is None) or (_omp_num_threads > 1):
    warning('OMP_NUM_THREADS is not set or is set to a value greater than 1,'
            ' we suggest setting OMP_NUM_THREADS=1 to improve performance')
del _openblas_lib, _openblas_dll, _omp_num_threads, os, cdll, find_library

# Stop profiling Firedrake import
if _is_logging:
    _init_event.end()
    del _init_event
del _is_logging
