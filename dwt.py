from PIL import Image
import numpy as np

def haar_dwt2(image_array):
  hs = image_array.shape[0] // 2

  LL = np.zeros((hs, hs))
  LH = np.zeros((hs, hs))
  HL = np.zeros((hs, hs))
  HH = np.zeros((hs, hs))

  for i in range(hs):
    for j in range(hs):
      coeff = image_array[i*2:i*2+2, j*2:j*2+2]
      a, b, c, d = (coeff[0,0], coeff[0,1], coeff[1,0], coeff[1,1])
      LL[i,j] = (a+b+c+d) / 4
      LH[i,j] = (b+d-a-c) / 4
      HL[i,j] = (c+d-a-b) / 4
      HH[i,j] = (b+c-a-d) / 4
  
  return (LL, LH, HL, HH)

def haar_idwt2(LL, LH, HL, HH):
  hs = LL.shape[0]
  fs = LL.shape[0] * 2
  source_array = np.zeros((fs, fs))
  
  for i in range(hs):
    for j in range(hs):
      a = LL[i,j] - LH[i,j] - HL[i,j] - HH[i,j]
      b = LL[i,j] + LH[i,j] - HL[i,j] + HH[i,j]
      c = LL[i,j] - LH[i,j] + HL[i,j] + HH[i,j]
      d = LL[i,j] + LH[i,j] + HL[i,j] - HH[i,j]
      source_array[i*2:i*2+2,j*2:j*2+2] = [[a,b],[c,d]]
  
  return source_array
