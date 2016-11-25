import glob
import numpy as np
import matplotlib.pyplot as plt
import pickle

onchip_matrices = glob.glob("onchip/*.pkl")
host_matrices = glob.glob("host/*.pkl")

assert len(onchip_matrices) == len(host_matrices)

for i, (o, h) in enumerate(zip(onchip_matrices, host_matrices)):
    with open(o, "r") as f:
        o_data = pickle.load(f)

    with open(h, "r") as f:
        h_data = pickle.load(f)


    # Unzip data
    if len(o_data) > 0:
        _, _, o_weights, o_delays = zip(*o_data)
    else:
        o_weights = []
        o_delays = []

    if len(h_data) > 0:
        _, _, h_weights, h_delays = zip(*h_data)
    else:
        h_weights = []
        h_delays = []


    print("%s - num:%u/%u, mean weight:%f/%f, mean delay:%f/%f" %
          (o, len(o_data), len(h_data),
           np.average(o_weights), np.average(h_weights),
           np.average(o_delays), np.average(h_delays)))

