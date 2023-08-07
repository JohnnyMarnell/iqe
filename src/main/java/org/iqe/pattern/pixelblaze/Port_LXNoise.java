package org.iqe.pattern.pixelblaze;

/**
 * Copied IntelliJ decompiled of heronarts.lx.utils.Noise, since more private methods
 * Namely, needed configurable perlin wrap
 *
 * PixelBlaze allow setting the perlin wraps, luckily this wasn't terrible to copy pasta add elsewhere
 */
public class Port_LXNoise {
    public static final int[] stb__perlin_randtab = new int[]{23, 125, 161, 52, 103, 117, 70, 37, 247, 101, 203, 169, 124, 126, 44, 123, 152, 238, 145, 45, 171, 114, 253, 10, 192, 136, 4, 157, 249, 30, 35, 72, 175, 63, 77, 90, 181, 16, 96, 111, 133, 104, 75, 162, 93, 56, 66, 240, 8, 50, 84, 229, 49, 210, 173, 239, 141, 1, 87, 18, 2, 198, 143, 57, 225, 160, 58, 217, 168, 206, 245, 204, 199, 6, 73, 60, 20, 230, 211, 233, 94, 200, 88, 9, 74, 155, 33, 15, 219, 130, 226, 202, 83, 236, 42, 172, 165, 218, 55, 222, 46, 107, 98, 154, 109, 67, 196, 178, 127, 158, 13, 243, 65, 79, 166, 248, 25, 224, 115, 80, 68, 51, 184, 128, 232, 208, 151, 122, 26, 212, 105, 43, 179, 213, 235, 148, 146, 89, 14, 195, 28, 78, 112, 76, 250, 47, 24, 251, 140, 108, 186, 190, 228, 170, 183, 139, 39, 188, 244, 246, 132, 48, 119, 144, 180, 138, 134, 193, 82, 182, 120, 121, 86, 220, 209, 3, 91, 241, 149, 85, 205, 150, 113, 216, 31, 100, 41, 164, 177, 214, 153, 231, 38, 71, 185, 174, 97, 201, 29, 95, 7, 92, 54, 254, 191, 118, 34, 221, 131, 11, 163, 99, 234, 81, 227, 147, 156, 176, 17, 142, 69, 12, 110, 62, 27, 255, 0, 194, 59, 116, 242, 252, 19, 21, 187, 53, 207, 129, 64, 135, 61, 40, 167, 237, 102, 223, 106, 159, 197, 189, 215, 137, 36, 32, 22, 5, 23, 125, 161, 52, 103, 117, 70, 37, 247, 101, 203, 169, 124, 126, 44, 123, 152, 238, 145, 45, 171, 114, 253, 10, 192, 136, 4, 157, 249, 30, 35, 72, 175, 63, 77, 90, 181, 16, 96, 111, 133, 104, 75, 162, 93, 56, 66, 240, 8, 50, 84, 229, 49, 210, 173, 239, 141, 1, 87, 18, 2, 198, 143, 57, 225, 160, 58, 217, 168, 206, 245, 204, 199, 6, 73, 60, 20, 230, 211, 233, 94, 200, 88, 9, 74, 155, 33, 15, 219, 130, 226, 202, 83, 236, 42, 172, 165, 218, 55, 222, 46, 107, 98, 154, 109, 67, 196, 178, 127, 158, 13, 243, 65, 79, 166, 248, 25, 224, 115, 80, 68, 51, 184, 128, 232, 208, 151, 122, 26, 212, 105, 43, 179, 213, 235, 148, 146, 89, 14, 195, 28, 78, 112, 76, 250, 47, 24, 251, 140, 108, 186, 190, 228, 170, 183, 139, 39, 188, 244, 246, 132, 48, 119, 144, 180, 138, 134, 193, 82, 182, 120, 121, 86, 220, 209, 3, 91, 241, 149, 85, 205, 150, 113, 216, 31, 100, 41, 164, 177, 214, 153, 231, 38, 71, 185, 174, 97, 201, 29, 95, 7, 92, 54, 254, 191, 118, 34, 221, 131, 11, 163, 99, 234, 81, 227, 147, 156, 176, 17, 142, 69, 12, 110, 62, 27, 255, 0, 194, 59, 116, 242, 252, 19, 21, 187, 53, 207, 129, 64, 135, 61, 40, 167, 237, 102, 223, 106, 159, 197, 189, 215, 137, 36, 32, 22, 5};
    public static final byte[] stb__perlin_randtab_grad_idx = new byte[]{7, 9, 5, 0, 11, 1, 6, 9, 3, 9, 11, 1, 8, 10, 4, 7, 8, 6, 1, 5, 3, 10, 9, 10, 0, 8, 4, 1, 5, 2, 7, 8, 7, 11, 9, 10, 1, 0, 4, 7, 5, 0, 11, 6, 1, 4, 2, 8, 8, 10, 4, 9, 9, 2, 5, 7, 9, 1, 7, 2, 2, 6, 11, 5, 5, 4, 6, 9, 0, 1, 1, 0, 7, 6, 9, 8, 4, 10, 3, 1, 2, 8, 8, 9, 10, 11, 5, 11, 11, 2, 6, 10, 3, 4, 2, 4, 9, 10, 3, 2, 6, 3, 6, 10, 5, 3, 4, 10, 11, 2, 9, 11, 1, 11, 10, 4, 9, 4, 11, 0, 4, 11, 4, 0, 0, 0, 7, 6, 10, 4, 1, 3, 11, 5, 3, 4, 2, 9, 1, 3, 0, 1, 8, 0, 6, 7, 8, 7, 0, 4, 6, 10, 8, 2, 3, 11, 11, 8, 0, 2, 4, 8, 3, 0, 0, 10, 6, 1, 2, 2, 4, 5, 6, 0, 1, 3, 11, 9, 5, 5, 9, 6, 9, 8, 3, 8, 1, 8, 9, 6, 9, 11, 10, 7, 5, 6, 5, 9, 1, 3, 7, 0, 2, 10, 11, 2, 6, 1, 3, 11, 7, 7, 2, 1, 7, 3, 0, 8, 1, 1, 5, 0, 6, 10, 11, 11, 0, 2, 7, 0, 10, 8, 3, 5, 7, 1, 11, 1, 0, 7, 9, 0, 11, 5, 10, 3, 2, 3, 5, 9, 7, 9, 8, 4, 6, 5, 7, 9, 5, 0, 11, 1, 6, 9, 3, 9, 11, 1, 8, 10, 4, 7, 8, 6, 1, 5, 3, 10, 9, 10, 0, 8, 4, 1, 5, 2, 7, 8, 7, 11, 9, 10, 1, 0, 4, 7, 5, 0, 11, 6, 1, 4, 2, 8, 8, 10, 4, 9, 9, 2, 5, 7, 9, 1, 7, 2, 2, 6, 11, 5, 5, 4, 6, 9, 0, 1, 1, 0, 7, 6, 9, 8, 4, 10, 3, 1, 2, 8, 8, 9, 10, 11, 5, 11, 11, 2, 6, 10, 3, 4, 2, 4, 9, 10, 3, 2, 6, 3, 6, 10, 5, 3, 4, 10, 11, 2, 9, 11, 1, 11, 10, 4, 9, 4, 11, 0, 4, 11, 4, 0, 0, 0, 7, 6, 10, 4, 1, 3, 11, 5, 3, 4, 2, 9, 1, 3, 0, 1, 8, 0, 6, 7, 8, 7, 0, 4, 6, 10, 8, 2, 3, 11, 11, 8, 0, 2, 4, 8, 3, 0, 0, 10, 6, 1, 2, 2, 4, 5, 6, 0, 1, 3, 11, 9, 5, 5, 9, 6, 9, 8, 3, 8, 1, 8, 9, 6, 9, 11, 10, 7, 5, 6, 5, 9, 1, 3, 7, 0, 2, 10, 11, 2, 6, 1, 3, 11, 7, 7, 2, 1, 7, 3, 0, 8, 1, 1, 5, 0, 6, 10, 11, 11, 0, 2, 7, 0, 10, 8, 3, 5, 7, 1, 11, 1, 0, 7, 9, 0, 11, 5, 10, 3, 2, 3, 5, 9, 7, 9, 8, 4, 6, 5};
    public static final float[][] stb__perlin_grad_basis = new float[][]{{1.0F, 1.0F, 0.0F}, {-1.0F, 1.0F, 0.0F}, {1.0F, -1.0F, 0.0F}, {-1.0F, -1.0F, 0.0F}, {1.0F, 0.0F, 1.0F}, {-1.0F, 0.0F, 1.0F}, {1.0F, 0.0F, -1.0F}, {-1.0F, 0.0F, -1.0F}, {0.0F, 1.0F, 1.0F}, {0.0F, -1.0F, 1.0F}, {0.0F, 1.0F, -1.0F}, {0.0F, -1.0F, -1.0F}};

    public Port_LXNoise() {
    }

    public static float stb__perlin_lerp(float a, float b, float t) {
        return a + (b - a) * t;
    }

    public static int stb__perlin_fastfloor(float a) {
        int ai = (int)a;
        return a < (float)ai ? ai - 1 : ai;
    }

    public static float stb__perlin_grad(int grad_idx, float x, float y, float z) {
        float[] grad = stb__perlin_grad_basis[grad_idx];
        return grad[0] * x + grad[1] * y + grad[2] * z;
    }

    public static float stb__perlin_ease(float a) {
        return ((a * 6.0F - 15.0F) * a + 10.0F) * a * a * a;
    }

    public static float stb_perlin_noise3_internal(float x, float y, float z, int x_wrap, int y_wrap, int z_wrap, int seed) {
        int x_mask = x_wrap - 1 & 255;
        int y_mask = y_wrap - 1 & 255;
        int z_mask = z_wrap - 1 & 255;
        int px = stb__perlin_fastfloor(x);
        int py = stb__perlin_fastfloor(y);
        int pz = stb__perlin_fastfloor(z);
        int x0 = px & x_mask;
        int x1 = px + 1 & x_mask;
        int y0 = py & y_mask;
        int y1 = py + 1 & y_mask;
        int z0 = pz & z_mask;
        int z1 = pz + 1 & z_mask;
        x -= (float)px;
        float u = stb__perlin_ease(x);
        y -= (float)py;
        float v = stb__perlin_ease(y);
        z -= (float)pz;
        float w = stb__perlin_ease(z);
        int r0 = stb__perlin_randtab[x0 + seed];
        int r1 = stb__perlin_randtab[x1 + seed];
        int r00 = stb__perlin_randtab[r0 + y0];
        int r01 = stb__perlin_randtab[r0 + y1];
        int r10 = stb__perlin_randtab[r1 + y0];
        int r11 = stb__perlin_randtab[r1 + y1];
        float n000 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r00 + z0], x, y, z);
        float n001 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r00 + z1], x, y, z - 1.0F);
        float n010 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r01 + z0], x, y - 1.0F, z);
        float n011 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r01 + z1], x, y - 1.0F, z - 1.0F);
        float n100 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r10 + z0], x - 1.0F, y, z);
        float n101 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r10 + z1], x - 1.0F, y, z - 1.0F);
        float n110 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r11 + z0], x - 1.0F, y - 1.0F, z);
        float n111 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r11 + z1], x - 1.0F, y - 1.0F, z - 1.0F);
        float n00 = stb__perlin_lerp(n000, n001, w);
        float n01 = stb__perlin_lerp(n010, n011, w);
        float n10 = stb__perlin_lerp(n100, n101, w);
        float n11 = stb__perlin_lerp(n110, n111, w);
        float n0 = stb__perlin_lerp(n00, n01, v);
        float n1 = stb__perlin_lerp(n10, n11, v);
        return stb__perlin_lerp(n0, n1, u);
    }

    public static float stb_perlin_noise3(float x, float y, float z, int x_wrap, int y_wrap, int z_wrap) {
        return stb_perlin_noise3_internal(x, y, z, x_wrap, y_wrap, z_wrap, 0);
    }

    public static float stb_perlin_noise3_seed(float x, float y, float z, int x_wrap, int y_wrap, int z_wrap, int seed) {
        return stb_perlin_noise3_internal(x, y, z, x_wrap, y_wrap, z_wrap, seed);
    }

    public static float stb_perlin_ridge_noise3(float x, float y, float z, float lacunarity, float gain, float offset, int octaves) {
        float frequency = 1.0F;
        float prev = 1.0F;
        float amplitude = 0.5F;
        float sum = 0.0F;

        for(int i = 0; i < octaves; ++i) {
            float r = stb_perlin_noise3_internal(x * frequency, y * frequency, z * frequency, 0, 0, 0, i);
            r = offset - Math.abs(r);
            r *= r;
            sum += r * amplitude * prev;
            prev = r;
            frequency *= lacunarity;
            amplitude *= gain;
        }

        return sum;
    }

    public static float stb_perlin_fbm_noise3(float x, float y, float z, float lacunarity, float gain, int octaves) {
        float frequency = 1.0F;
        float amplitude = 1.0F;
        float sum = 0.0F;

        for(int i = 0; i < octaves; ++i) {
            sum += stb_perlin_noise3_internal(x * frequency, y * frequency, z * frequency, 0, 0, 0, i) * amplitude;
            frequency *= lacunarity;
            amplitude *= gain;
        }

        return sum;
    }

    public static float stb_perlin_turbulence_noise3(float x, float y, float z, float lacunarity, float gain, int octaves) {
        float frequency = 1.0F;
        float amplitude = 1.0F;
        float sum = 0.0F;

        for(int i = 0; i < octaves; ++i) {
            float r = stb_perlin_noise3_internal(x * frequency, y * frequency, z * frequency, 0, 0, 0, i) * amplitude;
            sum += Math.abs(r);
            frequency *= lacunarity;
            amplitude *= gain;
        }

        return sum;
    }

    public static float stb_perlin_noise3_wrap_nonpow2(float x, float y, float z, int x_wrap, int y_wrap, int z_wrap, int seed) {
        int px = stb__perlin_fastfloor(x);
        int py = stb__perlin_fastfloor(y);
        int pz = stb__perlin_fastfloor(z);
        int x_wrap2 = x_wrap != 0 ? x_wrap : 256;
        int y_wrap2 = y_wrap != 0 ? y_wrap : 256;
        int z_wrap2 = z_wrap != 0 ? z_wrap : 256;
        int x0 = px % x_wrap2;
        int y0 = py % y_wrap2;
        int z0 = pz % z_wrap2;
        if (x0 < 0) {
            x0 += x_wrap2;
        }

        if (y0 < 0) {
            y0 += y_wrap2;
        }

        if (z0 < 0) {
            z0 += z_wrap2;
        }

        int x1 = (x0 + 1) % x_wrap2;
        int y1 = (y0 + 1) % y_wrap2;
        int z1 = (z0 + 1) % z_wrap2;
        x -= (float)px;
        float u = stb__perlin_ease(x);
        y -= (float)py;
        float v = stb__perlin_ease(y);
        z -= (float)pz;
        float w = stb__perlin_ease(z);
        int r0 = stb__perlin_randtab[x0];
        r0 = stb__perlin_randtab[r0 + seed];
        int r1 = stb__perlin_randtab[x1];
        r1 = stb__perlin_randtab[r1 + seed];
        int r00 = stb__perlin_randtab[r0 + y0];
        int r01 = stb__perlin_randtab[r0 + y1];
        int r10 = stb__perlin_randtab[r1 + y0];
        int r11 = stb__perlin_randtab[r1 + y1];
        float n000 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r00 + z0], x, y, z);
        float n001 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r00 + z1], x, y, z - 1.0F);
        float n010 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r01 + z0], x, y - 1.0F, z);
        float n011 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r01 + z1], x, y - 1.0F, z - 1.0F);
        float n100 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r10 + z0], x - 1.0F, y, z);
        float n101 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r10 + z1], x - 1.0F, y, z - 1.0F);
        float n110 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r11 + z0], x - 1.0F, y - 1.0F, z);
        float n111 = stb__perlin_grad(stb__perlin_randtab_grad_idx[r11 + z1], x - 1.0F, y - 1.0F, z - 1.0F);
        float n00 = stb__perlin_lerp(n000, n001, w);
        float n01 = stb__perlin_lerp(n010, n011, w);
        float n10 = stb__perlin_lerp(n100, n101, w);
        float n11 = stb__perlin_lerp(n110, n111, w);
        float n0 = stb__perlin_lerp(n00, n01, v);
        float n1 = stb__perlin_lerp(n10, n11, v);
        return stb__perlin_lerp(n0, n1, u);
    }
}

