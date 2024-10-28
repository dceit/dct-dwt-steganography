from PIL import Image
import numpy as np
import random
from scipy.fftpack import dct, idct
from util import mid_band_mask, correlate
from dwt import haar_dwt2, haar_idwt2

np.set_printoptions(formatter={'float': lambda x: "{0:0.2f}".format(x)})

block = 4
gain = 16

np.random.seed(2)
mask = mid_band_mask(block)
P_0 = mask * np.random.randint(-gain, gain, (block,block))
P_1 = mask * np.random.randint(-gain, gain, (block,block))

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

size = 512

img = Image.open("steg.jpg").resize((size, size), 1).convert('L')
image_array = np.array(img.getdata(), dtype=np.float32).reshape((size,size))

LL, LH, HL, HH = haar_dwt2(image_array)
decoded_msg = decode_dct(HL)
bin_str = "".join(map(str, decoded_msg))
src_str = [ chr(int(bin_str[i:i+8], 2)) for i in range(0, len(bin_str), 8) ]
print("".join(src_str))
