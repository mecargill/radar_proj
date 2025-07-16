import spidev
#from collections import deque
import time
import statistics
from matplotlib import pyplot as plt

PI_SPI_LENGTH = 4096
SIGNAL = b'\x64\x01'
num_bytes = 1*(PI_SPI_LENGTH-2)
downsample = int(num_bytes/2/10000)
if downsample == 0:
	downsample = 1



input("Hit enter to start capturing\n")

try:
	spi = spidev.SpiDev()
	spi.open(0, 0)
	spi.max_speed_hz = 20 * 10**6
	spi.mode = 0b00

	rx = []
	
	print("waiting for stm32")
	while 100 not in rx:
		rx = spi.xfer2([0xFF] * PI_SPI_LENGTH)
		rx = spi.xfer2([0xFF] * PI_SPI_LENGTH)
		
	print("detected stm32, receiving now")

	signal_index = -1
	rolling_buf = bytearray()
	result = bytearray()
	xfer_count = 0
	
	start = time.perf_counter()
	while len(result) < num_bytes:
			rolling_buf.extend(spi.xfer2([0xFF] * PI_SPI_LENGTH))
			xfer_count += 1
					
			signal_index = rolling_buf.find(SIGNAL)
			if signal_index >= 0 and signal_index + PI_SPI_LENGTH < len(rolling_buf):
				result.extend(rolling_buf[signal_index+len(SIGNAL):signal_index+PI_SPI_LENGTH])
				rolling_buf = rolling_buf[signal_index+PI_SPI_LENGTH:]
			
			
				
	tot_time = time.perf_counter() - start		
	spi.close()	
	
except KeyboardInterrupt:
	spi.close()


print("Done. Processing now")


print(f"recieved {len(result)} bytes")	

#print(result[:])
print(f"Pi estimated data rate: {xfer_count*PI_SPI_LENGTH*8/tot_time/1000000} Mbps. ADC estimated data rate: {len(result)*8/tot_time/1000000} Mbps. sample rate: {len(result)/2/tot_time/1000} ksps")
converted = []

for i in range(int(len(result)/2)):
	val = (result[2*i])*256  + result[2*i + 1]
	if val < 4096:
		converted.append(3.3*val/4096)
print("Std dev of voltages: ", statistics.stdev(converted))


y = converted[::downsample]
x = range(len(y))
plt.scatter(x, y, s=1)
#plt.ylim(0, 3.3)
plt.show()




"""
code to save: 
#length is num of things including current one to check
length = 15
converted = [-1]*(num_samples+length-1)
last = deque()
for i in range(length):
	last.append(0)
for i in range(num_samples-1, -1, -1):
	converted[i] = int((rx[2*i])*256 + (rx[2*i + 1] & 0b11110000))
	last.pop()
	last.appendleft(converted[i])
	if len(set(last)) == 1:
		converted[i] = -1
		
	
				
converted = [num for num in converted if num >= 0]
num_adc_samples = len(converted)				
print(f"We received {num_adc_samples*2} adc valid bytes in {time} seconds. that's {num_adc_samples} 12 bit voltage samples")
print(f"We estimate adc sample time to be {num_adc_samples/time/1000} ksps and the data rate to be {num_adc_samples*16/time/1000000} Mbps")
\
y = converted
x = range(len(y))	
plt.scatter(x, y)
#plt.ylim(0, 3.3)
plt.show()
"""
