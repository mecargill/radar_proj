print("Loading libraries...")
import spidev
import time
from datetime import datetime as dt
import numpy as np
from matplotlib import pyplot as plt
from multiprocessing import Queue, Process


PI_SPI_LENGTH = 4096 #bytes
FFT_WINDOW_LENGTH = int(2*(0.5*(PI_SPI_LENGTH-2))) #measurements
FFT_STEP_SIZE = int(0.5*FFT_WINDOW_LENGTH) #measurements
SIGNAL = b'\x64\x01'
COLLECT_TIME = 10 #seconds

collect_bytes = int(COLLECT_TIME * 4.7 * 10**6 / 8) #4.7Mbps is about the data rate of the nucleo I measured at current settings
print(collect_bytes)
baseline = None

def read_spi(queue, collect_time):
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
	xfer_count = 0
	
	start = time.perf_counter()
	while time.perf_counter() - start < collect_time:
		result = bytearray()
		while len(result) < FFT_WINDOW_LENGTH*2:
			rolling_buf.extend(spi.xfer2([0xFF] * PI_SPI_LENGTH))
			xfer_count += 1
			signal_index = rolling_buf.find(SIGNAL)
			if signal_index >= 0 and signal_index + PI_SPI_LENGTH < len(rolling_buf):
				result.extend(rolling_buf[signal_index+len(SIGNAL):signal_index+PI_SPI_LENGTH])
				rolling_buf = rolling_buf[signal_index+PI_SPI_LENGTH:]
		queue.put(bytes(result))
	spi.close()	
	#signal to stop other process
	queue.put(None)
	if collect_time == COLLECT_TIME:
		print(f"Done reading. Estimated Pi {xfer_count*PI_SPI_LENGTH*8/COLLECT_TIME/1000000} Mbps")


def range_processing(queue, baseline):	
	if baseline is None:
		baseline = np.zeros(int(FFT_WINDOW_LENGTH/2) + 1)
		baseline_flag = True
	else:
		baseline_flag = False
		
	result = []
	data = queue.get()
	byte_ct = 0
	while data is not None:
		byte_ct += len(data)
		npy_data = np.frombuffer(data, dtype=">u2")
		
		
		windowed = npy_data * np.hanning(len(npy_data))
		spectrum = np.fft.rfft(windowed)
		mags = np.abs(np.abs(spectrum) - baseline)
		
		result.append(mags)
		
		data = queue.get()
	
	f_s = byte_ct/2/COLLECT_TIME/1000
	if not baseline_flag:
		print(f"There were {byte_ct} bytes recieved, thats STM {8*byte_ct/COLLECT_TIME/1000000} Mbps and {f_s} ksps")
	
	npy_result = np.vstack(result)
	print(npy_result.shape)
	if not baseline_flag:
		#avoid log of 0
		npy_result = 10*np.log10(npy_result + 1e-12)
		plt.figure()
		plt.imshow(npy_result.T, aspect='auto', origin='lower', cmap='hot', extent=[0, COLLECT_TIME, 0, f_s/2])
		plt.xlabel("Time (s)")
		plt.ylabel("Frequency (kHz)")
		plt.ylim(0, 20)
		plt.colorbar(label='Magnitude (dB)')
		plt.tight_layout()
		plt.show()
		
	else:
		
		queue.put(npy_result)
		
		print("Done taking baseline")
	
if input("Would you like to take a baseline msmt to zero out (y/n)?\n").rstrip().lower() == "y":
	#take baseline
	baseline_queue = Queue(maxsize=100)	

	spi_reader = Process(target=read_spi, args=(baseline_queue, 1))
	range_processor = Process(target=range_processing, args=(baseline_queue, None))
	spi_reader.start()
	range_processor.start()	
	spi_reader.join()
	baseline = baseline_queue.get().mean(axis=0)
	range_processor.join()	
	
else:
	#set baseline to zero
	baseline = np.zeros(int(FFT_WINDOW_LENGTH/2) + 1)


while input("Press enter to start collecting. Type 'exit' to exit\n").rstrip().lower() != "exit":
	
	#collect real data
	queue = Queue(maxsize=100)	

	spi_reader = Process(target=read_spi, args=(queue, COLLECT_TIME))
	range_processor = Process(target=range_processing, args=(queue, baseline))
	spi_reader.start()
	range_processor.start()	
	spi_reader.join()
	
	range_processor.join()	
	


