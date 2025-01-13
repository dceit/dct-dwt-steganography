"use strict";

import { dctApply, idctApply } from "./dct.js";
import { dwtApply, idwtApply } from "./dwt.js";
import { cyrb128, sfc32 } from "./rand.js";

const ouptut = document.getElementById("output");
const text = document.getElementById("text");
const imageUpload = document.getElementById("source");
const buffer = document.getElementById("buffer");
const display = document.getElementById("display");
const ctx = buffer.getContext("2d");

const gain = 4;
const mainSize = 512;

function encodeImage(image) {
  const message = text.value;
  const binaryString = message.split("").map((c) => c.charCodeAt(0).toString(2).padStart(8, 0)).join("").padEnd(1024, 0);
  
  const [ size, width, height ] = getPo2Size(image.width, image.height);
  
  buffer.width = width;
  buffer.height = height;
  ctx.drawImage(image, 0, 0, width, height);
  
  const imageData = ctx.getImageData(0, 0, size, size);
  const dataArray = new Float32Array(size * size);
  convertYCbCr(imageData, dataArray);
  recursiveEncode(dataArray, size, mainSize, binaryString);
  convertRGB(imageData, dataArray);
  ctx.putImageData(imageData, 0, 0);
  
  output.innerHTML = "Binary Encoding: " + binaryString;
  
  display.src = buffer.toDataURL();
}

function recursiveEncode(dataArray, currentSize, desiredSize, binaryString) {
  if (currentSize != desiredSize) {
    const [ LL, LH, HL, HH ] = dwtApply(dataArray, currentSize);
    recursiveEncode(LL, currentSize / 2, desiredSize, binaryString);
    idwtApply(dataArray, currentSize, LL, LH, HL, HH);
  } else {
    const [ LL, LH, HL, HH ] = dwtApply(dataArray, currentSize);
    const [ LL2, LH2, HL2, HH2 ] = dwtApply(HH, currentSize);
    imageEncode(HH2, currentSize / 4, binaryString);
    idwtApply(HH, currentSize / 2, LL2, LH2, HL2, HH2);
    idwtApply(dataArray, currentSize, LL, LH, HL, HH);
  }
}

function decodeImage(image) {
  const [ size, width, height ] = getPo2Size(image.width, image.height);
  
  c.width = width;
  c.height = height;
  ctx.drawImage(image, 0, 0, width, height);
  
  const imageData = ctx.getImageData(0, 0, size, size);
  const dataArray = new Float32Array(size * size);
  convertYCbCr(imageData, dataArray);
  const decodedMessage = recursiveDecode(dataArray, size, mainSize);
  const binaryString = decodedMessage.join("");
  const asciiString = convertASCII(binaryString);
  
  output.innerHTML = "Decoded ASCII: " + asciiString;
  output.innerHTML += "<br>";
  output.innerHTML += "Binary Decoding: " + binaryString;
}

function recursiveDecode(dataArray, currentSize, desiredSize) {
  if (currentSize != desiredSize) {
    const [ LL, LH, HL, HH ] = dwtApply(dataArray, currentSize);
    return recursiveDecode(LL, currentSize / 2, desiredSize);
  } else {
    const [ LL, LH, HL, HH ] = dwtApply(dataArray, currentSize);
    const [ LL2, LH2, HL2, HH2 ] = dwtApply(HH, currentSize / 2);
    return imageDecode(HH2, currentSize / 4);
  }
}

function convertASCII(binaryString) {
  let res = "";
  
  while (binaryString.length > 0) {
    const block = binaryString.substring(0, 8);
    res += String.fromCharCode(parseInt(block, 2));
    binaryString = binaryString.substring(8);
  }
  return res;
}

function convertYCbCr(imageData, dataArray) {
  for (let i = 0; i < dataArray.length; i++) {
    const R = imageData.data[i * 4 + 0];
    const G = imageData.data[i * 4 + 1]
    const B = imageData.data[i * 4 + 2];
    dataArray[i] = 0.299 * R + 0.587 * G + 0.114 * B;
  }
}

function convertRGB(imageData, dataArray) {
  for (let i = 0; i < dataArray.length; i++) {
    const R = imageData.data[i * 4 + 0];
    const G = imageData.data[i * 4 + 1]
    const B = imageData.data[i * 4 + 2];
    
    const Y = dataArray[i];
    const Cb = 128 - 0.168736 * R - 0.331264 * G + 0.5 * B;
    const Cr = 128 + 0.5 * R - 0.418688 * G - 0.081312 * B;
    
    const nR = Y + 1.402 * (Cr - 128);
    const nG = Y - 0.344136 * (Cb - 128) - 0.714136 * (Cr - 128);
    const nB = Y + 1.772 * (Cb - 128);
    
    imageData.data[i * 4 + 0] = Math.round(nR);
    imageData.data[i * 4 + 1] = Math.round(nG);
    imageData.data[i * 4 + 2] = Math.round(nB);
  }
}

function imageEncode(dataArray, size, binaryString) {
  const S_0 = cyrb128("seed for p0");
  const S_1 = cyrb128("seed for p1");

  const P_0 = sfc32(S_0[0], S_0[1], S_0[2], S_0[3]);
  const P_1 = sfc32(S_1[0], S_1[1], S_1[2], S_1[3]);
  
  let offset = 0;
  
  for (let y = 0; y < size; y += 4) {
    for (let x = 0; x < size; x += 4) {
      const noiseVectorSelect = {
        "0": nextNoiseVector(P_0),
        "1": nextNoiseVector(P_1)
      };
      
      const bit = binaryString[offset++];
      
      dctEncode(dataArray, size, x, y, noiseVectorSelect[bit]);
    }
  }
}

function imageDecode(dataArray, size) {
  const S_0 = cyrb128("seed for p0");
  const S_1 = cyrb128("seed for p1");

  const P_0 = sfc32(S_0[0], S_0[1], S_0[2], S_0[3]);
  const P_1 = sfc32(S_1[0], S_1[1], S_1[2], S_1[3]);
  
  const bitArray = [];
  
  for (let y = 0; y < size; y += 4) {
    for (let x = 0; x < size; x += 4) {
      const noiseVector0 = nextNoiseVector(P_0);
      const noiseVector1 = nextNoiseVector(P_1);
      
      const bit = dctDecode(dataArray, size, x, y, noiseVector0, noiseVector1);
      bitArray.push(bit);
    }
  }
  
  return bitArray;
}

function dctDecode(dataArray, size, x, y, noiseVector0, noiseVector1) {
  const dctSquare = new Float32Array(4 * 4);
  readData(dctSquare, size, dataArray, x, y);
  dctApply(dctSquare);
  
  const dataVector = readDataVector(dctSquare);
  
  const r0 = pearsonCorrelation(dataVector, noiseVector0);
  const r1 = pearsonCorrelation(dataVector, noiseVector1);
  
  return r0 < r1 ? 1 : 0;
}

function readDataVector(dataArray) {
  const dataVector = new Float32Array(10);
  
  let N = 0;
  
  for (let i = 2; i < 4; i++) {
    for (let j = 0; j < i + 1; j++) {
      const x = i - j;
      const y = j;
      dataVector[N] = dataArray[y * 4 + x];
      N++;
    }
  }

  for (let j = 0; j < 3; j++) {
    const x = 3 - j;
    const y = 1 + j;
    dataVector[N] = dataArray[y * 4 + x];
    N++;
  }
  
  return dataVector;
}

function noiseApply(outputArray, noiseVector) {
  let N = 0;
  
  for (let i = 2; i < 4; i++) {
    for (let j = 0; j < i + 1; j++) {
      const x = i - j;
      const y = j;
      outputArray[y * 4 + x] += noiseVector[N++];
    }
  }
  
  for (let j = 0; j < 3; j++) {
    const x = 3 - j;
    const y = 1 + j;
    outputArray[y * 4 + x] += noiseVector[N++];
  }
}

function pearsonCorrelation(X, Y) {
  const N = X.length;
  
  let x_bar = 0.0;
  let y_bar = 0.0;
  
  for (let i = 0; i < N; i++) {
    x_bar += X[i];
    y_bar += Y[i];
  }
  
  x_bar /= N;
  y_bar /= N;
  
  let sumDiffProd = 0.0;
  let sumSquareDiffX = 0.0;
  let sumSquareDiffY = 0.0;
  
  for (let i = 0; i < N; i++) {
    sumDiffProd += (X[i] - x_bar) * (Y[i] - y_bar);
    sumSquareDiffX += Math.pow(X[i] - x_bar, 2);
    sumSquareDiffY += Math.pow(Y[i] - y_bar, 2);
  }
  
  return sumDiffProd / Math.sqrt(sumSquareDiffX * sumSquareDiffY);
}

function nextNoiseVector(noise) {
  const noiseVector = new Float32Array(10);
  for (let i = 0; i < noiseVector.length; i++) {
    noiseVector[i] = (noise() * 2.0 - 1.0) * gain;
  }
  return noiseVector;
}

function dctEncode(dataArray, size, x, y, noiseVector) {
  const dctSquare = new Float32Array(4 * 4);
  readData(dctSquare, size, dataArray, x, y);
  
  dctApply(dctSquare);
  noiseApply(dctSquare, noiseVector);
  idctApply(dctSquare);
  
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 4; j++) {
      dataArray[(y + i) * size + (x + j)] = dctSquare[i * 4 + j];
    }
  }
}

function readData(outputArray, size, dataArray, x, y) {
  for (let i = 0; i < 4; i++) {
    for (let j = 0; j < 4; j++) {
      outputArray[i * 4 + j] = dataArray[(y + i) * size + (x + j)];
    }
  }
}

function getPo2Size(width, height) {
  if (height < width) {
    const size = Math.max(Math.pow(2, Math.ceil(Math.log(height)/Math.log(2))), mainSize);
    return [ size, Math.round(size * width / height), size ];
  } else {
    const size = Math.max(Math.pow(2, Math.ceil(Math.log(width)/Math.log(2))), mainSize);
    return [ size, size, Math.round(size * height / width) ];
  }
}

document.getElementById("encode").addEventListener("click", () => {
  const image = new Image();
  image.src = window.URL.createObjectURL(imageUpload.files[0]);
  image.onload = () => encodeImage(image);
});

document.getElementById("decode").addEventListener("click", () => {
  const image = new Image();
  image.src = window.URL.createObjectURL(imageUpload.files[0]);
  image.onload = () => decodeImage(image);
});

document.getElementById("save").addEventListener("click", () => {
  window.open(display.src, "_blank");
});

window.addEventListener("paste", (e) => {
  const data = (e || e.originalEvent).clipboardData;
  const blob = data.items[0].getAsFile();
  const reader = new FileReader();
  reader.onload = (e) => {
    const image = new Image();
    image.src = e.target.result;
    image.onload = () => encodeImage(image);
  };
  reader.readAsDataURL(blob);
});
