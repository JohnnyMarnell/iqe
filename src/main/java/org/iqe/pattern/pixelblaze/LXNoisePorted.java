package org.iqe.pattern.pixelblaze;

import static org.iqe.pattern.pixelblaze.Port_LXNoise.stb_perlin_noise3_internal;

/** PixelBlaze allow setting the perlin wraps, luckily this wasn't terrible to copy pasta add */
public class LXNoisePorted {
    public static float stb_perlin_ridge_noise3(
            float x, float y, float z,
            float lacunarity, float gain, float offset,
            int octaves,

            int x_wrap, int y_wrap, int z_wrap
    ) {
        float frequency = 1.0F;
        float prev = 1.0F;
        float amplitude = 0.5F;
        float sum = 0.0F;

        for(int i = 0; i < octaves; ++i) {
            float r = stb_perlin_noise3_internal(x * frequency, y * frequency, z * frequency,
                    x_wrap, y_wrap, z_wrap, i);
            r = offset - Math.abs(r);
            r *= r;
            sum += r * amplitude * prev;
            prev = r;
            frequency *= lacunarity;
            amplitude *= gain;
        }

        return sum;
    }

    public static float stb_perlin_turbulence_noise3(
            float x, float y, float z, float lacunarity, float gain, int octaves,

            int x_wrap, int y_wrap, int z_wrap) {
        float frequency = 1.0F;
        float amplitude = 1.0F;
        float sum = 0.0F;

        for(int i = 0; i < octaves; ++i) {
            float r = stb_perlin_noise3_internal(x * frequency, y * frequency, z * frequency,
                    x_wrap, y_wrap, z_wrap, i) * amplitude;
            sum += Math.abs(r);
            frequency *= lacunarity;
            amplitude *= gain;
        }

        return sum;
    }
}
