import numpy as np

def mid_band_mask(block):
  A = np.zeros((block, block))
  
  for i in range(block-2, block):
    for j in range(i + 1):
      gx = i - j
      gy = j
      A[gy, gx] = 1.0

  for i in range(block-2, block):
    for j in range(i + 1):
      gx = block - 1 - j
      gy = block - 1 - i + j
      A[gy, gx] = 1.0
  
  return A

def correlate(x, y):
  x_bar = np.mean(x)
  y_bar = np.mean(y)

  top = np.sum((x - x_bar) * (y - y_bar))
  bot = np.sqrt(np.sum(np.power(x - x_bar, 2)) * np.sum(np.power(y - y_bar, 2)))

  return top/bot
