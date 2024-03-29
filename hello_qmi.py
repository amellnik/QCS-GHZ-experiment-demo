"""
Simple script to verify that the QMI is working.
After you have activated the virtual environment that comes with your QMI
(using source ~/.virtualenvs/venv/bin/activate), run this as:

    python hello_qmi.py [<qcname>]

Options:

    <qcname>        Name of a quantum computer available through the pyQuil API
                    [default: 9q-generic-qvm]

"""
import math
from typing import Optional

from pyquil import Program, get_qc
from pyquil.api import QVM
from pyquil.api._devices import list_lattices
from pyquil.gates import RX, MEASURE
from pyquil.quil import Pragma


def query_device(device_name) -> dict:
    """
    Try to query the device from QCS. Return the lattice dict if it exists, or
    or None otherwise.
    """
    lattices = list_lattices()
    if device_name in list(lattices.keys()):
        return lattices[device_name]
    return None


def get_active_lattice() -> Optional[str]:
    """
    Try to query which lattice we're engaged to from QCS. Returns the lattice
    name if available, otherwise None.
    """
    from rpcq import Client
    from pyquil.api._config import PyquilConfig
    try:
        qcc = Client(endpoint=PyquilConfig().qpu_compiler_url, timeout=1)
        return qcc.call("get_config_info")["lattice_name"]
    except:
        return None


def hello_qmi(device_name: str = "9q-generic-qvm", shots: int = 5) -> None:
    """
    Get acquainted with your quantum computer by asking it to perform a simple
    coin-toss experiment. Involve 3 qubits in this experiment, and ask each one
    to give `shots` many results.

    :param device_name: The name of a quantum computer which can be retrieved
                        from `pyquil.api.get_qc()`. To find a list of all
                        devices, you can use `pyquil.api.list_devices()`.
    """
    # Initialize your Quil program
    program = Program()
    # Allow the compiler to re-index to use available qubits, if necessary.
    program += Pragma('INITIAL_REWIRING', ['"GREEDY"'])
    device = query_device(device_name)
    if device is not None:
        # device_name refers to a real (QPU) device, so let's construct
        # the program from the device's qubits.
        readout = program.declare('ro', 'BIT', len(device['qubits']))
        for qubit in device['qubits'].values():
            program += RX(math.pi / 2, qubit)
        for idx, qubit in enumerate(device['qubits'].values()):
            program += MEASURE(qubit, readout[idx])
    else:
        # device_name refers to a non-real (QVM) device, so let's construct
        # the program from arbitrary qubits, e.g. 0, 1, and 2

        # Declare 3 bits of memory space for the readout results of all three qubits
        readout = program.declare('ro', 'BIT', 3)
        # For each qubit, apply a pulse to move the qubit's state halfway between
        # the 0 state and the 1 state
        program += RX(math.pi / 2, 0)
        program += RX(math.pi / 2, 1)
        program += RX(math.pi / 2, 2)
        # Add measurement instructions to measure the qubits and record the result
        # into the respective bit in the readout register
        program += MEASURE(0, readout[0])
        program += MEASURE(1, readout[1])
        program += MEASURE(2, readout[2])

    # This tells the program how many times to run the above sequence
    program.wrap_in_numshots_loop(shots)

    # Get the quantum computer we want to run our experiment on
    qc = get_qc(device_name)

    # Compile the program, specific to which quantum computer we are using
    compiled_program = qc.compile(program)

    # Run the program and get the shots x 3 array of results
    results = qc.run(compiled_program)
    # Print the results. We expect to see (shots x 3) random 0's and 1's
    print(f"Your{' virtual' if isinstance(qc.qam, QVM) else ''} quantum "
          f"computer, {device_name}, greets you with:\n", results)


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        hello_qmi(device_name=sys.argv[1].strip())
    else:
        hello_qmi()
