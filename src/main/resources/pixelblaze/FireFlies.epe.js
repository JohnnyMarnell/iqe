// This is a fork of Sparks, 
//  - modified to slow down the sparks
//  - gave them a longer lifetime 
//  - allowed them to loop from one ned to the other

sparkHue = .05;
sparkSaturation = 1;
numSparks = 1 + (pixelCount / 10);
decay = 0.99 ;
maxSpeed = 0.4
newThreshhold = 0.01

sparks = array(numSparks);
sparkX = array(numSparks);
pixels = array(pixelCount);

export function beforeRender(delta) {
  delta *= .1;
  
  for (i = 0; i < pixelCount; i++)
    pixels[i] = pixels[i] * 0.9;
  
  for (i = 0; i < numSparks; i++) {
    if (sparks[i] >= -newThreshhold && sparks[i] <= newThreshhold) {
      sparks[i] = (maxSpeed/2) - random(maxSpeed);
      sparkX[i] = random(pixelCount);
    }
    
    sparks[i] *= decay;
    sparkX[i] += sparks[i] *  delta;
    
    if (sparkX[i] >= pixelCount) {
      sparkX[i] = 0;
    }
    
    if (sparkX[i] < 0) {
      sparkX[i] = pixelCount - 1;
    }
    
    pixels[floor(sparkX[i])] += sparks[i];
  }
}

export function render(index) {
  v = pixels[index];
  hsv(sparkHue, sparkSaturation, v * v * 10)
}

