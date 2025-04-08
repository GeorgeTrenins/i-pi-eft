# Computing electronic friction along a trajectory

This example uses FHI-aims to drive an NVE trajectory (H atom diffusing through Pd). The hydrogen block of the electronic friction tensor is calculated on the fly and communicated to i-PI. At present, i-PI simply prints the EFT to file

## Input files

 * Pd4H.xyz: initial geometry

 * basisset.in: default _light_ settings 

 * control.in.template: header of _control.in_, the penultimate line tells FHI-aims to send i-PI the value of that EFT at 0.01 eV; the final line specifies the unix socket (same address as in _input.xml_, the dummy port number 1234 is not used but has to be specified)

 * geometry.in: initial geometry in FHI-aims format; the coordinates are ingored, but the `calculate_friction` flag controls which block of the EFT is computed

 * input.xml: i-PI input file:

   - line 5 activates printing of the EFT

   - lines 12--14 control communication with FHI-aims


## Running the simulation

First, modify _run.sh_ according to your own setup. In the current version

  * Line 4 sets up the Intel oneAPI environment (this very likely has to be modified)

  * Lines 5--9 locate the project root directory - **keep as is**

  * Line 9 activates the project's virtual python environment (modify as needed)

  * Line 10 puts the i-pi executables in the system path - **keep**

  * Lines 11--30 set up the input files, removes any lingering files used for socket communication in the previous run, etc - **keep**

  * Lines 31..33 launch the FHI-aims client - modify as needed

