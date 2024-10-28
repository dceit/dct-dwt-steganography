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

size = 512

file = input("image: ")
msg = input("message: ")
source_msg = [ int(y) for y in "".join([bin(x)[2:].zfill(8) for x in map(ord, msg)]) ] + [0] * (4096 - len(msg) * 8)

img = Image.open(file).resize((size, size), 1).convert('L')
image_array = np.array(img.getdata(), dtype=np.float32).reshape((size,size))

LL, LH, HL, HH = haar_dwt2(image_array)
HL = encode_dct(HL, source_msg)
output_array = haar_idwt2(LL, LH, HL, HH)

print("encoded into steg.jpg")

res = Image.fromarray(output_array).convert("RGB")
res.save("steg.jpg")
res.show()
