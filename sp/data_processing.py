import numpy as np
import os
from matplotlib import pyplot as plt
import matplotlib.animation as animation




#load data
data_folder = "raw_data/max_range"

baseline_file = "data_25-07-10_08_23_37_fs_294_raw.npy"
baseline_fs = 294

data_file = "data_25-07-10_08_25_30_fs_292_raw.npy" #refl
#data_file = "data_25-07-10_08_28_52_fs_294_raw.npy" #human
#data_file = "../ramp_signal/data_25-07-08_12_24_00_fs_293_raw.npy" #chirp
data_fs = 292

baseline = np.load(os.path.join(data_folder, baseline_file))
data = np.load(os.path.join(data_folder, data_file))

#make a 2D Freq vs time array
def spectrogram(npy_data_total, win_length, step_size, index=0):
	result = []
	while index + win_length <= len(npy_data_total):
		npy_data = npy_data_total[index:index+win_length]
		windowed = npy_data * np.hanning(len(npy_data))
		#windowed = npy_data
		spectrum = np.fft.rfft(windowed)
		#mags = np.abs(spectrum)
		
		result.append(spectrum)
		index += step_size
	#mags are 1d arrays with ascending frequency bins
	#vstacking them makes the shape bin #, frequency
	#for imshow, we want time (aka bin #) on the x axis, so we take the transpose
	npy_result = np.vstack(result).T
	return npy_result
#make in terms of z scores and clip
def zscore_spec(spectrogram, baseline, min_percentile=0, max_percentile=100):
	spectrogram = np.abs(spectrogram)
	baseline = np.abs(baseline)
	means = np.mean(baseline, axis=1)
	devs = np.std(baseline, axis=1)
	z_scores = (spectrogram - means.reshape(-1, 1)) * (devs**-1).reshape(-1, 1)
	sorted = np.sort(z_scores.flatten())
	min_index = int((min_percentile/100)*(len(sorted)-1))
	max_index = int((max_percentile/100)*(len(sorted)-1))
	min = sorted[min_index]
	max = sorted[max_index]
	return np.clip(z_scores, min, max)
	

#plot the freq vs time array
def plot_spec(spectrogram, f_s, length):
	
	plt.figure()
	plt.imshow(spectrogram,
				aspect='auto',
				origin='lower',
				cmap='hot',
				extent=[0, length/(f_s*1000), 0, 1.2* f_s/2])
	plt.xlabel("Time (s)")
	plt.ylabel("Range (m)")
	plt.ylim(0, 40)
	plt.colorbar(label='Magnitude')
	plt.tight_layout()

#this returns a list of doppler plots at different points in time
def doppler(spectrogram, segment_length):
	result = []
	i = 0
	while i+segment_length <= spectrogram.shape[1]:
		time_slice = spectrogram[:,i:i+segment_length]

		for j in range(time_slice.shape[0]):
			row = time_slice[j]
			spectrum = np.fft.fftshift(np.fft.fft(row*np.kaiser(len(row), 5)))
			time_slice[j] = spectrum
		result.append(time_slice)
		i = i + segment_length
	return result


def plot_doppler(doppler, f_s):
	
	fig, ax = plt.subplots()
	img = ax.imshow(doppler,
				aspect='auto',
				origin='lower',
				cmap='hot',
				
				extent=[-1, 1, 0, (f_s/2)*1.2])
	ax.set_xlabel("Velocity (normalized)")
	ax.set_ylabel("Range (m)")
	ax.set_ylim((0, 30))
	fig.colorbar(img, ax=ax, label='Magnitude')
	return fig, img
		
def doppler_gif(doppler_arrs, f_s, name):
	doppler_arrs = [np.log10(np.abs(arr) + 1e-15) for arr in doppler_arrs]
	fig, img = plot_doppler(doppler_arrs[0], f_s)
	def update(i):
		img.set_data(doppler_arrs[i])
		return[img]
	ani = animation.FuncAnimation(fig, update, frames=len(doppler_arrs), blit=True)
	ani.save(name, writer='pillow', fps=10)

chirp_len = 251
data_spec = spectrogram(data, chirp_len, chirp_len)
bl_spec = spectrogram(baseline, chirp_len, chirp_len)
#z_data_spec = zscore_spec(data_spec, bl_spec, min_percentile=90, max_percentile=99)
#plot_spec(z_data_spec, data_fs, len(data))
#plt.show()
doppler_arrs = doppler(data_spec, 251)
doppler_gif(doppler_arrs, data_fs, "sp/data_doppler.gif")

doppler_arrs = doppler(bl_spec, 251)
doppler_gif(doppler_arrs, baseline_fs, "sp/baseline_doppler.gif")





