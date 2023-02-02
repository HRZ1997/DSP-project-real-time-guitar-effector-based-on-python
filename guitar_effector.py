# final DSP lab project
# real time electrical guitar effector with GUI
# implement through pyAudio, Tkinter, FFT
# contributed by Haoran Zhang

import pyaudio, wave, struct, math
import numpy as np
import scipy.signal
from matplotlib import pyplot as plt
import tkinter as Tk
import wave
import time
import math

# define functions
# FFT concolution
def fft_conv(signal_block, impulse_response):
	n = len(signal_block) + len(impulse_response) - 1
	N = 2 ** int(np.log2(n) + 1)
	SIGNAL = np.fft.fft(signal_block, N)
	IMPULSE = np.fft.fft(impulse_response, N)
	return np.fft.ifft(SIGNAL * IMPULSE)[:n]

# GUI functions
def fun_quit():			# quit function
	global CONTINUE
	print('Bye.')
	CONTINUE = False

# switch functions
	# compressor switch funtion
def comp_switch():
    global compressor_switch
     
    # Determine is on or off
    if compressor_switch:
        B_comp.config(image = off)
        compressor_switch = False
    else:
        B_comp.config(image = on)
        compressor_switch = True

	# distortion switch funtion
def dist_switch():
    global distortion_switch
     
    # Determine is on or off
    if distortion_switch:
        B_dist.config(image = off)
        distortion_switch = False
    else:
        B_dist.config(image = on)
        distortion_switch = True

	# overdrive switch funtion
def over_switch():
    global overdrive_switch
     
    # Determine is on or off
    if overdrive_switch:
        B_over.config(image = off)
        overdrive_switch = False
    else:
        B_over.config(image = on)
        overdrive_switch = True

  # delay, vibrato, flanger are all delay based effect
  # so users are allowed to apply only one of them at one time
	# delay switch funtion
def dly_switch():
    global delay_switch, vibrato_switch, flanger_switch
    global buffer, kw, kr
     
    # Determine is on or off
    if delay_switch:
      B_delay.config(image = off)
      delay_switch = False
    else:
      B_delay.config(image = on)
      B_vibrato.config(image = off)
      B_flanger.config(image = off)
      delay_switch = True
      vibrato_switch = False
      flanger_switch = False
      
      # initialize buffer and index
      buffer = BUFFER_LEN * [0]
      kw = int(0.5 * BUFFER_LEN)

	# vibrato switch funtion
def vbrt_switch():
    global delay_switch, vibrato_switch, flanger_switch
    global buffer, kw, kr, vbrt_phase, vibrato_depth

    # Determine is on or off
    if vibrato_switch:
      B_vibrato.config(image = off)
      vibrato_switch = False
    else:

      B_vibrato.config(image = on)
      B_delay.config(image = off)
      B_flanger.config(image = off)
      vibrato_switch = True
      delay_switch = False
      flanger_switch = False

      # initialize buffer and index
      vibrato_depth.set(0)
      buffer = BUFFER_LEN * [0]
      kw = int(0.5*BUFFER_LEN)
      kr = 0
      vbrt_phase = 0

	# flanger switch funtion
def flngr_switch():
    global delay_switch, vibrato_switch, flanger_switch
    global buffer, kw, kr, vbrt_phase
     
    # Determine is on or off
    if flanger_switch:
      B_flanger.config(image = off)
      flanger_switch = False
    else:
      B_flanger.config(image = on)
      B_delay.config(image = off)
      B_vibrato.config(image = off)
      flanger_switch = True
      delay_switch = False
      vibrato_switch = False

      vibrato_depth.set(0)
      buffer = BUFFER_LEN * [0]
      kw = int(0.5*BUFFER_LEN)
      kr = 0
      vbrt_phase = 0

def preset1():
	global comp_switch, dist_switch, over_switch, delay_switch, vibrato_switch, flanger_switch
	global B_comp, B_dist, B_over, B_delay, B_vibrato, B_flanger

	# compressor on
	B_comp.config(image = on)
	compressor_switch = True

	compressor_threshold.set(-6)
	compressor_ratio.set(8)

  # distortion off
	B_dist.config(image = off)
	distortion_switch = False

  # overdrive on
	B_over.config(image = on)
	overdrive_switch = True

	overdrive_gain.set(4000)
	overdrive_threshold.set(800)

  # delay on, vibrato & flanger off
	B_delay.config(image = on)
	B_vibrato.config(image = off)
	B_flanger.config(image = off)
	delay_switch = True
	vibrato_switch = False
	flanger_switch = False
  
  # initialize buffer and index
	buffer = BUFFER_LEN * [0]
	kw = int(0.5 * BUFFER_LEN)

	delay_time.set(200)
	delay_feedback.set(300)


# effector function
	# compressor
def compressor(block, threshold, ratio):
	global compressor_switch

	if compressor_switch:
		for i in range(BLOCKLEN):
			dBFS = 20 * np.log10(np.abs(block[i])/MAXVALUE)
			if dBFS > threshold:
				temp = block[i]
				dB_compress = (dBFS - threshold) / ratio + threshold
				block[i] = 10 ** (dB_compress / 20) * MAXVALUE * (np.abs(block[i])/block[i])

	return block

def distortion(block, gain, threshold):
	global distortion_switch

	if distortion_switch:
		threshold_val = threshold * MAXVALUE
		for i in range(BLOCKLEN):
			block[i] *= gain
			if block[i] > threshold_val:
				block[i] = threshold_val
			elif block[i] < -threshold_val:
				block[i] = -threshold_val

	return block

def overdrive(block, gain, threshold):
	global overdrive_switch

	if overdrive_switch:
		threshold_val = threshold * MAXVALUE
		for i in range(BLOCKLEN):

			temp = block[i] * gain / MAXVALUE
			if block[i] > 0:
				block[i] = threshold_val * (1 - math.exp(-temp))
			elif block[i] < 0:
				block[i] = - threshold_val * (1 - math.exp(temp))

	return block


		# delay based module
def delay(block, time, feedback):
	global buffer, kw, kr

	N_delay = int( RATE * time )

	if N_delay > kw:
		kr = kw + BUFFER_LEN - N_delay
	else:
		kr = kw - N_delay

	for i in range(BLOCKLEN):
		block[i] = block[i] + feedback * buffer[kr]
		buffer[kw] = block[i]
		kr += 1
		if kr >= BUFFER_LEN:
			kr = 0
		kw += 1
		if kw >= BUFFER_LEN:
			kw = 0

	return block

		# vibrato based module
def vibrato(block, depth, rate, gain):
	global buffer, kw, kr, vbrt_phase, vbrt_dpth_prev
	global vibrato_switch, flanger_switch

	if vibrato_switch or flanger_switch:
		
		if depth != vbrt_dpth_prev:
			kr = kw - RATE * depth
			if kr < 0:
				kr += BUFFER_LEN

			vbrt_dpth_prev = depth
			vbrt_phase = 0

		for i in range(BLOCKLEN):
			kr_prev = int(math.floor(kr))
			kr_next = kr_prev + 1
			
			if kr_next == BUFFER_LEN:
				kr_next = 0

			buffer[kw] = block[i]
			if vibrato_switch:
				block[i] = gain* ((buffer[kr_next] - buffer[kr_prev]) * (kr - kr_prev) + buffer[kr_prev])
			elif flanger_switch:
				block[i] = gain* ((buffer[kr_next] - buffer[kr_prev]) * (kr - kr_prev) + buffer[kr_prev]) + block[i]

			kw = kw + 1
			if kw == BUFFER_LEN:
				kw = 0

			kr = kw - RATE * depth * (1 + math.sin(2 * math.pi * rate * vbrt_phase / RATE))
			if kr < 0:
				kr = kr + BUFFER_LEN
			
			vbrt_phase += 1
			if vbrt_phase > RATE/rate:
				vbrt_phase = 0

	return block

def out_gain(block, gain):
	for i in range(BLOCKLEN):
		block[i] = block[i] * gain

	return block

def enviroment(block, ir_block):
	global overlap_add_buffer

	conv_block = fft_conv(block, ir_block)
	for i in range(BLOCKLEN):
		block[i] = conv_block[i] + overlap_add_buffer[i]

	for i in range(BLOCKLEN, OVERLAPLEN):
		overlap_add_buffer[i - BLOCKLEN] = overlap_add_buffer[i] + conv_block[i]

	for i in range(OVERLAPLEN - BLOCKLEN, OVERLAPLEN):
		overlap_add_buffer[i] = 0

	return block

# Define Tkinter root
root = Tk.Tk()
root.geometry('1200x800')

# import button images
on = Tk.PhotoImage(file = "on.png")
off = Tk.PhotoImage(file = "off.png")

# import support image
guitar = Tk.PhotoImage(file = "guitar.png")
arrow = Tk.PhotoImage(file = "arrow.png")

# sampling parameters
WIDTH		= 4			# bytes per sample
CHANNELS	= 1			# mono
RATE		= 48000		# sample rate (samples/second), high enough for high quality

BLOCKLEN = 512		# length of block
MAXVALUE = 2**31 - 1

# circular buffer for delay modules
BUFFER_LEN = 48000
buffer = BUFFER_LEN * [0]

# Buffer (delay line) indices
kr = 0  										# read index
kw = int(0.5 * BUFFER_LEN)  # write index (initialize to middle of buffer)

# define play parameter
gain = 2

# Define parameters and set the default value
	# main loop control
CONTINUE = True

	# compressor
compressor_threshold = Tk.IntVar()		#compressor threshold
compressor_ratio = Tk.IntVar()				#compressor ratio
compressor_switch = False

compressor_threshold.set(-6)
compressor_ratio.set(5)

	# distortion
distortion_gain = Tk.DoubleVar()
distortion_threshold = Tk.DoubleVar()
distortion_switch = False

distortion_gain.set(1500)
distortion_threshold.set(0.8)

	# overdrive
overdrive_gain = Tk.DoubleVar()
overdrive_threshold = Tk.DoubleVar()
overdrive_switch = False

overdrive_gain.set(1500)
overdrive_threshold.set(800)

	# delay
delay_time = Tk.DoubleVar()						# delay time
delay_feedback = Tk.DoubleVar()				# delay feedback
delay_switch = False

delay_time.set(500)
delay_feedback.set(500)

	# vibrato
vibrato_depth = Tk.DoubleVar()						# vibrato depth
vibrato_rate = Tk.DoubleVar()				# vibrato rate
vibrato_gain = Tk.DoubleVar()
vibrato_switch = False
flanger_switch = False

vibrato_depth.set(0)
vibrato_rate.set(1)
vibrato_gain.set(1000)

 # output gain
output_gain = Tk.DoubleVar()
output_gain.set(1000)

# Define widgets
	# All purpose
L_title = Tk.Label(root, text = 'DSP project - Guitar Effector', font=("Arial", 22))
L_guitar = Tk.Label(root, image = guitar)
L_guitar_input = Tk.Label(root, text = 'Guitar Input', font=("Arial", 20))
L_arrow1 = Tk.Label(root, image = arrow)
L_arrow2 = Tk.Label(root, image = arrow)
L_arrow3 = Tk.Label(root, image = arrow)
L_arrow4 = Tk.Label(root, image = arrow)
L_arrow5 = Tk.Label(root, image = arrow)
L_arrow6 = Tk.Label(root, image = arrow)
L_or = Tk.Label(root, text = 'OR', font=("Arial", 20))
B_quit = Tk.Button(root, text = 'Quit', command = fun_quit)

	# compressor
		# compressor parameter slide
S_compressor_threshold = Tk.Scale(root, variable = compressor_threshold, from_ = -18, to = -1)
S_compressor_ratio = Tk.Scale(root, variable = compressor_ratio, from_ = 2, to = 10)

		# compressor label
L_compressor = Tk.Label(root, text = 'Compressor', font=("Arial", 20))
L_compressor_threshold = Tk.Label(root, text = 'threshold(dB)')
L_compressor_ratio = Tk.Label(root, text = 'ratio')
		# compressor switch button
B_comp = Tk.Button(root, image = off, bd = 0, command = comp_switch)

	# distortion
		# distortion parameter slide
S_distortion_gain = Tk.Scale(root, variable = distortion_gain, from_ = 1000, to = 5000)
S_distortion_threshold = Tk.Scale(root, variable = distortion_threshold, from_ = 500, to = 1000)

		# distortion label
L_distortion = Tk.Label(root, text = 'Distortion', font=("Arial", 20))
L_distortion_gain = Tk.Label(root, text = 'gain(* 1e-3)')
L_distortion_threshold = Tk.Label(root, text = 'threshold(* 1e-3)')
		# distortion switch button
B_dist = Tk.Button(root, image = off, bd = 0, command = dist_switch)

	# overdrive
		# overdrive parameter slide
S_overdrive_gain = Tk.Scale(root, variable = overdrive_gain, from_ = 800, to = 5000)
S_overdrive_threshold = Tk.Scale(root, variable = overdrive_threshold, from_ = 500, to = 1000)

		# overdrive label
L_overdrive = Tk.Label(root, text = 'Overdrive', font=("Arial", 20))
L_overdrive_gain = Tk.Label(root, text = 'gain(* 1e-3)')
L_overdrive_threshold = Tk.Label(root, text = 'threshold(* 1e-3)')
		# overdrive switch button
B_over = Tk.Button(root, image = off, bd = 0, command = over_switch)

	# delay module
		# delay parameter slide
S_delay_time = Tk.Scale(root, variable = delay_time, from_ = 50, to = 900)
S_delay_feedback = Tk.Scale(root, variable = delay_feedback, from_ = 0, to = 800)

		# delay label
L_delay = Tk.Label(root, text = 'Delay', font=("Arial", 20))
L_delay_time = Tk.Label(root, text = 'time(ms)')
L_delay_feedback = Tk.Label(root, text = 'feedback(* 1e-3)')

		# delay switch button
B_delay = Tk.Button(root, image = off, bd = 0, command = dly_switch)

	# vibrato
		# vibrato parameter slide
S_vibrato_depth = Tk.Scale(root, variable = vibrato_depth, from_ = 0, to = 200)
S_vibrato_rate = Tk.Scale(root, variable = vibrato_rate, from_ = 1, to = 6)
S_vibrato_gain = Tk.Scale(root, variable = vibrato_gain, from_ = 0, to = 1000)

		# vibrato label
L_vibrato = Tk.Label(root, text = 'Vibrato&Flanger', font=("Arial", 20))
L_vibrato_depth = Tk.Label(root, text = 'depth(ms)')
L_vibrato_rate = Tk.Label(root, text = 'rate(Hz)')
L_vibrato_gain = Tk.Label(root, text = 'gain(* 1e-3)')
L_vibrato_switch = Tk.Label(root, text = 'vibrato')
L_flanger_switch = Tk.Label(root, text = 'flanger')

		# vibrato switch button
B_vibrato = Tk.Button(root, image = off, bd = 0, command = vbrt_switch)
B_flanger = Tk.Button(root, image = off, bd = 0, command = flngr_switch)

S_output_gain = Tk.Scale(root, variable = output_gain, from_ = 0, to = 2000)
L_output_gain = Tk.Label(root, text = 'output gain((* 1e-3)')

B_preset1 = Tk.Button(root, text = 'Preset 1', command = preset1)

# Place widgets
base_x = 400
base_y = 50
gap_x = 250
gap_y = 300
	# All purpose Button
L_guitar.place( x = 20, y = base_y + 20)
L_guitar_input.place( x = 100, y = base_y)
L_arrow1.place( x = 250, y = 100)
L_arrow2.place( x = 500, y = 100)
L_arrow3.place( x = 750, y = 100)
L_arrow4.place( x = 1000, y = 100)
L_arrow5.place( x = 80, y = 100 + gap_y)
L_or.place( x = 420, y = 120 + gap_y)
L_arrow6.place( x = 700, y = 100 + gap_y)
L_title.place( x = 400, y = 10)
B_quit.place( x = 1100, y = 750)

	# compressor
L_compressor.place(x = base_x, y = base_y)
S_compressor_threshold.place( x = base_x, y = base_y + 40)
S_compressor_ratio.place(x = base_x + 90, y = base_y + 40)
L_compressor_threshold.place( x= base_x - 10, y = base_y + 140)
L_compressor_ratio.place( x = base_x + 70, y = base_y + 140)
B_comp.place( x = base_x, y = base_y + 170)

	# distortion
L_distortion.place(x = base_x + gap_x, y = base_y)
S_distortion_gain.place( x = base_x + gap_x, y = base_y + 40)
S_distortion_threshold.place(x = base_x + gap_x + 70, y = base_y + 40)
L_distortion_gain.place( x= base_x + gap_x - 10, y = base_y + 140)
L_distortion_threshold.place( x = base_x + gap_x + 70, y = base_y + 140)
B_dist.place( x = base_x + gap_x, y = base_y + 170)

	# overdrive
L_overdrive.place(x = base_x + gap_x * 2, y = base_y)
S_overdrive_gain.place( x = base_x + gap_x * 2, y = base_y + 40)
S_overdrive_threshold.place(x = base_x + gap_x * 2 + 70, y = base_y + 40)
L_overdrive_gain.place( x= base_x + gap_x * 2 - 10, y = base_y + 140)
L_overdrive_threshold.place( x = base_x + gap_x * 2 + 70, y = base_y + 140)
B_over.place( x = base_x + gap_x * 2, y = base_y + 170)

	# delay
L_delay.place(x = gap_x, y = base_y + gap_y)
S_delay_time.place( x = gap_x, y = base_y + gap_y + 40)
S_delay_feedback.place(x = gap_x + 70, y = base_y + gap_y + 40)
L_delay_time.place( x= gap_x - 10, y = base_y + gap_y + 140)
L_delay_feedback.place( x = gap_x + 70, y = base_y + gap_y + 140)
B_delay.place( x = gap_x, y = base_y + gap_y + 170)

	# vibrato
L_vibrato.place(x = gap_x * 2, y = base_y + gap_y)
S_vibrato_depth.place( x = gap_x * 2, y = base_y + gap_y + 40)
S_vibrato_rate.place(x = gap_x * 2 + 70, y = base_y + gap_y + 40)
S_vibrato_gain.place(x = gap_x * 2 + 120, y = base_y + gap_y + 40)
L_vibrato_depth.place( x= gap_x * 2, y = base_y + gap_y + 140)
L_vibrato_rate.place( x = gap_x * 2 + 70, y = base_y + gap_y + 140)
L_vibrato_gain.place(x = gap_x * 2 + 140, y = base_y + gap_y + 140)
L_vibrato_switch.place(x = gap_x * 2, y = base_y + gap_y + 170)
B_vibrato.place( x = gap_x * 2, y = base_y + gap_y + 200)
L_flanger_switch.place(x = gap_x * 2, y = base_y + gap_y + 280)
B_flanger.place(x = gap_x * 2, y = base_y + gap_y + 310)

 # output gain
S_output_gain.place(x = gap_x * 3 + 100, y = base_y + gap_y + 40)
L_output_gain.place(x = gap_x * 3 + 100, y = base_y + gap_y + 140)

B_preset1.place(x = gap_x * 3 + 100, y = base_y + gap_y + 200)


# Create Pyaudio object
p = pyaudio.PyAudio()
PA_FORMAT = pyaudio.paInt32
stream = p.open(
  format = PA_FORMAT,  
  channels = CHANNELS, 
  rate = RATE,
  input = True, 
  output = True,
  frames_per_buffer = 64)


vbrt_dpth_prev = 0
vbrt_phase = 0
# main loop
while CONTINUE:
	root.update()

	comp_thrsh = compressor_threshold.get()
	comp_rt = compressor_ratio.get()

	dist_gain = distortion_gain.get() / 1000
	dist_threshold = distortion_threshold.get() / 1000

	over_gain = overdrive_gain.get() / 1000
	over_threshold = overdrive_threshold.get() / 1000

	dly_tm = delay_time.get()/1000
	dly_fdbk = delay_feedback.get()/1000

	vbrt_dpth = vibrato_depth.get()/1000
	vbrt_rt = vibrato_rate.get()
	vbrt_gn = vibrato_gain.get()/1000

	out_gn = output_gain.get()/1000

	input_bytes = stream.read(BLOCKLEN, exception_on_overflow = False)
	input_block = struct.unpack('i' * BLOCKLEN, input_bytes)

	preamp_block = np.array(input_block) * gain					# boost signal as preamp

	compress_block = compressor(preamp_block, comp_thrsh, comp_rt)

	distortion_block = distortion(compress_block, dist_gain, dist_threshold)

	overdrive_block = overdrive(distortion_block, over_gain, over_threshold)

	if delay_switch:
		delay_block = delay(overdrive_block, dly_tm, dly_fdbk)
	else: 
		delay_block = vibrato(overdrive_block, vbrt_dpth, vbrt_rt, vbrt_gn)

	output_block = out_gain(delay_block, out_gn)

	output_block = np.clip(output_block, -MAXVALUE, MAXVALUE)
	output_bytes = struct.pack('i' * BLOCKLEN, *output_block)

	stream.write(output_bytes)

stream.stop_stream()
stream.close()
p.terminate()

print('* Finished')
