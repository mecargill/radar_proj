import numpy as np
import os
from matplotlib import pyplot as plt
import matplotlib.animation as animation
from scipy import signal

F_0 = 2.4 * 10**9
C = 3 * 10**8

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
def spectrogram(npy_data_total, chirp_len, index=0, boundaries=[]):
	result = []
	for boundary in boundaries:
		slice_start = round(boundary)
		slice_end = slice_start + round(chirp_len)
		index = slice_end
		npy_data = npy_data_total[slice_start:slice_end]
		windowed = npy_data * np.hanning(len(npy_data))
		spectrum = np.fft.rfft(windowed)		
		result.append(spectrum)
	
	chirp_num = 0
	slice_start = round(index + chirp_num*chirp_len)
	slice_end = slice_start + round(chirp_len)
	while slice_end <= len(npy_data_total):
		npy_data = npy_data_total[slice_start:slice_end]
		windowed = npy_data * np.hanning(len(npy_data))
		spectrum = np.fft.rfft(windowed)		
		result.append(spectrum)
		chirp_num += 1
		slice_start = round(index + chirp_num*chirp_len)
		slice_end = round(index + chirp_num*chirp_len + chirp_len)
	
		
	#mags are 1d arrays with ascending frequency bins
	#vstacking them makes the shape bin #, frequency
	#for imshow, we want time (aka bin #) on the x axis, so we take the transpose
	npy_result = np.vstack(result).T
	#to account for triangle wave causing time reversal, we conjugate in the freq domain every other chirp
	npy_result[:, ::2] = np.conj(npy_result[:, ::2])
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
def doppler(spectrogram, segment_length, f_s, chirp_len):
	result = []
	times = []
	i = 0
	while i+segment_length <= spectrogram.shape[1]:
		time_slice = spectrogram[:,i:i+segment_length]
		for j in range(time_slice.shape[0]):
			row = time_slice[j]
			spectrum = np.fft.fftshift(np.fft.fft(row*np.hanning(len(row))))
			time_slice[j] = spectrum
		result.append(time_slice)
		times.append(chirp_len * (i)/(f_s*1000))
		i = i + segment_length
	return result, times

def z_score_doppler(doppler_arrs, min_percentile=0, max_percentile=100):
	doppler = np.abs(np.stack(doppler_arrs))
	means = np.mean(doppler, axis=0)[np.newaxis,:,:]
	devs = np.std(doppler, axis=0)[np.newaxis,:,:]
	z_scores = (doppler - means) #* (devs**-1)
	sorted = np.sort(z_scores.flatten())
	min_index = int((min_percentile/100)*(len(sorted)-1))
	max_index = int((max_percentile/100)*(len(sorted)-1))
	min = sorted[min_index]
	max = sorted[max_index]
	return np.clip(z_scores, min, max)

def plot_doppler(doppler, f_s, slow_time_T):
	vmax = C/slow_time_T/F_0/4
	fig, ax = plt.subplots()
	img = ax.imshow(doppler,
				aspect='auto',
				origin='lower',
				cmap='hot',
				
				extent=[-1*vmax, vmax, 0, (f_s/2)*1.2])
	ax.set_xlabel("Velocity (m/s)")
	ax.set_ylabel("Range (m)")
	ax.set_ylim((0, 30))
	ax.set_xlim((-3, 3))
	fig.colorbar(img, ax=ax, label='Magnitude')
	return fig, ax, img
		
def doppler_gif(doppler_arrs, f_s, chirp_len, times, name, gif_time=10):
	slow_time_T = chirp_len/(f_s*1000)
	fps = int(len(doppler_arrs)/gif_time)	
	fig, ax, img = plot_doppler(doppler_arrs[0], f_s, slow_time_T)
	ax.set_title(f"t = {times[0]} s")
	def update(i):
		img.set_data(doppler_arrs[i])
		ax.set_title(f"t = {times[i]:.2f} s")
		return[img]
	ani = animation.FuncAnimation(fig, update, frames=len(doppler_arrs), blit=True)
	ani.save(name, writer='pillow', fps=fps)



def find_chirps(data, data_fs, data_cutoff=len(data)):
	#get rid of the extraneous low frequencies, plus smooth out the noisy adc 
	b, a = signal.butter(7, 5 / (data_fs / 2), btype='high', analog=False)
	x = signal.filtfilt(b, a, data)
	x = np.convolve(x, np.ones(6)/6, mode='same')

	n=data_cutoff
	chirp_len = 251
	std_dev_co = 400
	next_est_pt = 718
	boundaries = []
	outer_reach = 240 #so len is that x2
	inner_reach = 200

	#take a first known mirror point (718) and make a window outer_reach in either direction
	#then slide an inner window along that, taking half reversed and dotting it with the other half
	#this finds the most mirrorlike point (also scaled by avg amplitude)
	outer_len = 2*outer_reach
	inner_len = 2*inner_reach
	while next_est_pt + outer_reach < n:
		outer_start = next_est_pt-outer_reach
		outer_end = next_est_pt+outer_reach
		outer_window = x[outer_start:outer_end]
		
		if np.std(outer_window) < std_dev_co:
			correlations = np.empty(outer_len - inner_len + 1)
			for inner_start in range(outer_len - inner_len + 1):
				inner_end = inner_start + inner_len
				inner_window = outer_window[inner_start:inner_end]
				correlations[inner_start] = np.dot(inner_window[:inner_reach], inner_window[inner_reach:][::-1])
			boundaries.append(outer_start + np.argmax(correlations) + inner_reach)
			
			next_est_pt = boundaries[-1] + chirp_len
		else:
			boundaries.append(next_est_pt)
			next_est_pt += chirp_len
	return boundaries, x
		
	
chirp_len = 250.80105368790768
boundaries, _ = find_chirps(data, data_fs)	

data_spec = spectrogram(data, chirp_len, boundaries=boundaries)
data_spec = np.log10(np.abs(data_spec))
plot_spec(data_spec, data_fs, len(data))
plt.show()







"""
doppler_arrs, times = doppler(data_spec, 600, data_fs, 251)
doppler_arrs = [np.log10(np.abs(arr) + 1e-15) for arr in doppler_arrs]
#doppler_arrs = z_score_doppler(doppler_arrs, 99.99, 100)

doppler_gif(doppler_arrs[:int(0.5*len(doppler_arrs)-2)], data_fs, chirp_len, times, "sp/data_doppler.gif", gif_time=5)
"""