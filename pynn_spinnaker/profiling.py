# Import modules
import matplotlib.cm as cm
import numpy as np

# Import functions
from scipy.stats import binned_statistic
from six import iteritems, iterkeys, itervalues


def print_summary(profiling_data, duration, dt=1.0):
    """
    Print a summary of the profiling data to standard out
    Showing how much time is spent in each profiler tag
    """
    timestep_bins = np.arange(0.0, duration, dt)

    # Summarise data for all tags
    for tag_name, times in profiling_data.iteritems():
        print("Tag:%s" % (tag_name))

        print("\tMean time per sample:%fms" % (np.average(times[1])))

        # Digitize the sample entry times into these bins
        sample_timestep_indices = np.digitize(times[0], timestep_bins)
        assert len(sample_timestep_indices) == len(times[1])

        # Calculate the average number of samples in each bin
        print("\tMean samples per timestep:%f" %
              (np.average(np.bincount(sample_timestep_indices))))

        # Determine the last sample time (if profiler runs out
        # Of space to write samples it may not be duration)
        last_sample_time = np.amax(sample_timestep_indices) + 1
        print("\tLast sample time:%fms" % (last_sample_time))

        # Sum durations of samples binned into ms timestep bibs
        total_sample_duration_per_timestep = binned_statistic(
            times[0], times[1], statistic="sum", bins=timestep_bins)[0]

        print("\tMean time per timestep:%fms" %
              (np.average(total_sample_duration_per_timestep)))


def plot_profile(profiling_data, axis):
    # Get a suitable colour array from current palette
    colours = cm.get_cmap()(np.linspace(0.0, 1.0, len(profiling_data)))

    # Plot profile
    for i, (t, c) in enumerate(zip(itervalues(profiling_data), colours)):
        for entry_time, duration in zip(t[0], t[1]):
            axis.bar(i, duration, bottom=entry_time,
                     width=1.0, linewidth=0, color=c)

    # Draw ticks
    axis.set_xticks([0.5 + float(i) for i in range(len(profiling_data))])
    axis.set_xticklabels(list(iterkeys(profiling_data)))


def filter_time(profile_data, min_time, max_time):
    filtered_profile_data = {}
    for tag_name, times in iteritems(profile_data):
        # Get indices of entry times which fall within time range
        filtered_indices = np.where(
            (times[0] >= float(min_time)) & (times[0] < float(max_time)))

        # Add entry times and durations, filtered by
        # new indices to filtered tag dictionary
        filtered_profile_data[tag_name] = (times[0][filtered_indices],
                                           times[1][filtered_indices])

    return filtered_profile_data


def write_csv_header(profiling_data, csv_writer, extra_column_headers):
    """
    Write header row for standard profiler format CSV file with extra
    column headers followed by tag names found in profiling_data
    """
    csv_writer.writerow(extra_column_headers + list(iterkeys(profiling_data)))


def write_csv_row(profiling_data, duration, dt, csv_writer,
                  extra_column_values):
    """
    Write a row into standard profiler format CSV with user values
    followed by mean times for each profiler tag extracted from profiling_data
    """
    timestep_bins = np.arange(0.0, duration, dt)

    # Calculate mean of all profiling tags
    mean_times = [np.average(binned_statistic(t[0], t[1], statistic="sum",
                                              bins=timestep_bins)[0])
                  for t in itervalues(profiling_data)]

    # Write extra column followed by means
    csv_writer.writerow(extra_column_values + mean_times)
