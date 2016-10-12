from rig.machine_control import MachineController
import numpy as np
import matplotlib.pyplot as plt
from StringIO import StringIO

# Load application
mc = MachineController("192.168.1.1")
mc.load_application("random.aplx", {(0, 0): set([1])})

# Wait for it to exit
mc.wait_for_cores_to_reach_state("exit", 1)

# Build a string IO from the IO buffer
input_data = StringIO(mc.get_iobuf(1, 0, 0))

# Stop the application
mc.send_signal("stop")

# Read data into numpy
data = np.genfromtxt(input_data, skip_header=1, delimiter=",")

# Extract column containing normally distributed samples
normal = data[:,1]

# Plot histogram
fig, axis = plt.subplots()
axis.hist(normal, 100)
plt.show()
