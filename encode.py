from PIL import Image
import numpy as np
import random
from scipy.fftpack import dct, idct
from util import mid_band_mask, correlate
from dwt import haar_dwt2, haar_idwt2
from math import *

np.set_printoptions(formatter={'float': lambda x: "{0:0.2f}".format(x)})

block = 4
gain = 8

np.random.seed(2)
mask = mid_band_mask(block)
P_0 = mask * np.random.randint(-gain, gain, (block,block))
P_1 = mask * np.random.randint(-gain, gain, (block,block))

def encode_dct(input_array, msg):
  offset = 0
  size = input_array.shape[0]
  output_array = np.zeros((size, size))
  for i in range(0, size, block):
    for j in range(0, size, block):
      kernel = P_0 if msg[offset % len(msg)] == 0 else P_1
      source_array = input_array[i:i+block, j:j+block]
      dct_array = dct(dct(source_array.T, norm="ortho").T, norm="ortho") + kernel
      inv_dct_array = idct(idct(dct_array.T, norm="ortho").T, norm="ortho")
      output_array[i:i+block, j:j+block] = inv_dct_array
      offset += 1
  return output_array

def decode_dct(input_array):
  size = input_array.shape[0]
  decoded_msg = []
  for i in range(0, size, block):
    for j in range(0, size, block):
      source_array = input_array[i:i+block, j:j+block]
      dct_array = dct(dct(source_array.T, norm="ortho").T, norm="ortho")
      r1 = correlate(dct_array * mask, P_0)
      r2 = correlate(dct_array * mask, P_1)
      bit = 1 if r1 < r2 else 0
      decoded_msg.append(bit)
  return decoded_msg

file = "ogey.jpg"
msg = "Hello World" * 20
source_msg = [ int(y) for y in "".join([bin(x)[2:].zfill(8) for x in map(ord, msg)]) ] + [0] * (4096 - len(msg) * 8)

img = Image.open(file)
width, height = img.size

if height < width:
  h = 2**(ceil(log(img.size[1])/log(2)))
  w = h * width // height
  size = h
else:
  w = 2**(ceil(log(img.size[0])/log(2)))
  h = w * height // width
  size = w

img = img.resize((w,h)).convert('L')
image_array = np.array(img.getdata(), dtype=np.float32).reshape((h,w))
sub_array = image_array[0:size,0:size]

def recursive_encode(sub_array):
  print(sub_array.shape)
  if sub_array.shape[0] != 512:
    LL, LH, HL, HH = haar_dwt2(sub_array)
    LL = recursive_encode(LL)
    return haar_idwt2(LL, LH, HL, HH)
  else:
    LL, LH, HL, HH = haar_dwt2(sub_array)
    LL2, LH2, HL2, HH2 = haar_dwt2(HH)
    HH2 = encode_dct(HH2, source_msg)
    HH = haar_idwt2(LL2, LH2, HL2, HH2)
    return haar_idwt2(LL, LH, HL, HH)

sub_array = recursive_encode(sub_array)

image_array[0:size,0:size] = sub_array

res = Image.fromarray(image_array).convert("RGB")
res.save("steg.jpg")
res.show()
