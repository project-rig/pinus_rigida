import glob
import numpy as np
import pickle
import matplotlib.pyplot as plt

#onchip_matrices = glob.glob("onchip/*.npy")
#host_matrices = glob.glob("host/*.npy")

#assert len(onchip_matrices) == len(host_matrices)


with open("onchip/weights_L5E_L23I.pkl", "r") as f:
        o_data = pickle.load(f)
with open("host/weights_L5E_L23I.pkl", "r") as f:
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

print("num:%u/%u, mean weight:%f/%f, mean delay:%f/%f" %
        (len(o_data), len(h_data),
        np.average(o_weights), np.average(h_weights),
        np.average(o_delays), np.average(h_delays)))

weight_fig, weight_axes = plt.subplots(2, sharex=True)
o_weight_hist, weight_bins = np.histogram(o_weights, bins=100)
h_weight_hist, _ = np.histogram(h_weights, bins=weight_bins)
weight_axes[0].set_title("On-chip")
weight_axes[0].bar(weight_bins[:-1], o_weight_hist, weight_bins[1] - weight_bins[0])
weight_axes[1].set_title("Host")
weight_axes[1].bar(weight_bins[:-1], h_weight_hist, weight_bins[1] - weight_bins[0])

delay_fig, delay_axes = plt.subplots(2, sharex=True)
o_delay_hist, delay_bins = np.histogram(o_delays, bins=np.arange(0.0, 10.0, 0.1))
h_delay_hist, _ = np.histogram(h_delays, bins=delay_bins)
delay_axes[0].set_title("On-chip")
delay_axes[0].bar(delay_bins[:-1], o_delay_hist, 0.1)
delay_axes[1].set_title("Host")
delay_axes[1].bar(delay_bins[:-1], h_delay_hist, 0.1)

#o_hist, o_bins = np.histogram(o_delays, bins=np.arange(0.0, 10.0, 0.1))
#h_hist, h_bins = np.histogram(h_delays, bins=o_bins)

    #axes[i, 0].set_title("%s - %u" % (o, np.sum(o_data)))
    #axes[i, 0].imshow(o_data)

    #axes[i, 1].set_title("%s - %u" % (h, np.sum(h_data)))
    #axes[i, 1].imshow(h_data)

#fig.tight_layout()
plt.show()
