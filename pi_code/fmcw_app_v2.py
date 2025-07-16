print("Loading libraries...")
import spidev
import time
from datetime import datetime as dt
import numpy as np
from matplotlib import pyplot as plt



PI_SPI_LENGTH = 4096 #bytes
FFT_WINDOW_LENGTH = int(2*(0.5*(PI_SPI_LENGTH-2))) #measurements
FFT_STEP_SIZE = int(0.5*FFT_WINDOW_LENGTH) #measurements
SIGNAL = b'\x64\x01'
COLLECT_TIME = 25 #seconds

#waits for the signal, reads for some time, then returns npy array of data + sample frequency
def read_spi(collect_time):
	spi = spidev.SpiDev()
	spi.open(0, 0)
	spi.max_speed_hz = 20 * 10**6
	spi.mode = 0b00
	
	rx = []
	
	print("Waiting for stm32")
	while SIGNAL[0] not in rx:
		rx = spi.xfer2([0xFF] * PI_SPI_LENGTH)
		rx = spi.xfer2([0xFF] * PI_SPI_LENGTH)
	print("Detected stm32, collecting data now")
	
	signal_index = -1
	rolling_buf = bytearray()
	result = bytearray()
	xfer_count = 0
	
	start = time.perf_counter()
	while time.perf_counter() - start < collect_time:
		rolling_buf.extend(spi.xfer2([0xFF] * PI_SPI_LENGTH))
		xfer_count += 1
		signal_index = rolling_buf.find(SIGNAL)
		if signal_index >= 0 and signal_index + PI_SPI_LENGTH < len(rolling_buf):
			result.extend(rolling_buf[signal_index+len(SIGNAL):signal_index+PI_SPI_LENGTH])
			rolling_buf = rolling_buf[signal_index+PI_SPI_LENGTH:]
	spi.close()	

	if collect_time == COLLECT_TIME:
		print(f"Done reading. Estimated Pi {xfer_count*PI_SPI_LENGTH*8/COLLECT_TIME/1000000} Mbps")
		f_s = len(result)/2/COLLECT_TIME/1000
		print(f"There were {len(result)} bytes recieved, thats STM {8*len(result)/COLLECT_TIME/1000000} Mbps and {f_s} ksps")
	npy_data = np.frombuffer(result, dtype=">u2")
	return npy_data, f_s

def spectrogram(npy_data_total):
	index = 0
	result = []
	while index + FFT_WINDOW_LENGTH <= len(npy_data_total):
		npy_data = npy_data_total[index:index+FFT_WINDOW_LENGTH]
		windowed = npy_data * np.hanning(len(npy_data))
		spectrum = np.fft.rfft(windowed)
		mags = np.abs(spectrum)
		
		result.append(mags)
		index += FFT_STEP_SIZE
	#mags are 1d arrays with ascending frequency bins
	#vstacking them makes the shape bin #, frequency
	#for imshow, we want time (aka bin #) on the x axis, so we take the transpose
	npy_result = np.vstack(result).T
	return npy_result


while input("Press enter to start collecting. Type 'exit' to exit\n").rstrip().lower() != "exit":
	
	npy_data, f_s = read_spi(COLLECT_TIME)	
	np.save(f"/home/frankedoodles/Documents/data/data_{dt.now().strftime('%y-%m-%d_%H_%M_%S')}_fs_{int(f_s)}_raw.npy", npy_data)
	npy_result = spectrogram(npy_data)
	
	#convert spectrogram magnitude to dB
	npy_result = 10*np.log10(npy_result + 1e-12)
	plt.figure()
	plt.imshow(npy_result, aspect='auto', origin='lower', cmap='hot', extent=[0, COLLECT_TIME, 0, f_s/2])
	plt.xlabel("Time (s)")
	plt.ylabel("Frequency (kHz)")
	plt.ylim(0, 25)
	plt.colorbar(label='Magnitude (dB)')
	plt.tight_layout()
	plt.show()
	


