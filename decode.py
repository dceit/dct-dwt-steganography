from PIL import Image
import numpy as np
import random
from scipy.fftpack import dct, idct
from util import mid_band_mask, correlate
from dwt import haar_dwt2, haar_idwt2
from math import *

np.set_printoptions(formatter={'float': lambda x: "{0:0.2f}".format(x)})

block = 4
gain = 12

np.random.seed(2)
mask = mid_band_mask(block)

def decode_dct(input_array):
  size = input_array.shape[0]
  decoded_msg = []
  for i in range(0, size, block):
    for j in range(0, size, block):
      P_0 = mask * np.random.randint(-gain, gain, (block,block))
      P_1 = mask * np.random.randint(-gain, gain, (block,block))
      source_array = input_array[i:i+block, j:j+block]
      dct_array = dct(dct(source_array.T, norm="ortho").T, norm="ortho")
      r1 = correlate(dct_array * mask, P_0)
      r2 = correlate(dct_array * mask, P_1)
      bit = 1 if r1 < r2 else 0
      decoded_msg.append(bit)
  return decoded_msg

def recursive_decode(sub_array):
  print(sub_array.shape)
  if sub_array.shape[0] != 512:
    LL, LH, HL, HH = haar_dwt2(sub_array)
    return recursive_decode(LL)
  else:
    LL, LH, HL, HH = haar_dwt2(sub_array)
    LL2, LH2, HL2, HH2 = haar_dwt2(HH)
    return decode_dct(HH2)

img = Image.open("steg.jpg")
width, height = img.size

if height < width:
  h = 2**(ceil(log(img.size[1])/log(2)))
  w = h * width // height
  size = h
else:
  w = 2**(ceil(log(img.size[0])/log(2)))
  h = w * height // width
  size = w

img = img.resize((w,h)).convert("YCbCr")
image_array = np.array(img.getdata(), dtype=np.float32).reshape((h,w,3))
sub_array = image_array[0:size,0:size,0]

decoded_msg = recursive_decode(sub_array)
bin_str = "".join(map(str, decoded_msg))
src_str = [ chr(int(bin_str[i:i+8], 2)) for i in range(0, len(bin_str), 8) ]
print("".join(src_str))
