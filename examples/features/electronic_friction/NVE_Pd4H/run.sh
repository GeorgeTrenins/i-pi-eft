#!/bin/bash -e

# set up the environment
source /opt/intel/oneapi/setvars.sh
APP_ROOT="$(readlink -fm "$0")"
for i in {1..5} ; do
    APP_ROOT="$(dirname ${APP_ROOT})"
done
source "${APP_ROOT}/.venv/bin/activate"
source "${APP_ROOT}/env.sh"

# prepare the input files
rm -f /tmp/ipi_pd4h-md.1

export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export MKL_DYNAMIC=FALSE
ulimit -s unlimited


cp control.in.template control.in
cat basisset.in >> control.in

i-pi input.xml &> log.i-pi & 
echo "# i-PI is running"

sleep_time=5
echo "# Waiting for ${sleep_time} (s) before executing driver"
sleep ${sleep_time}

AIMSHOME="${HOME}/software/FHIaims"
VERSION=250312
mpirun -n 6 "${AIMSHOME}/build_${VERSION}/aims.${VERSION}.scalapack.mpi.x" < /dev/null &> aims.out &
