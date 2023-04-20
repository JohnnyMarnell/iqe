import numpy as np
import math as math

def unit_sphere(dir):
    yaw, pitch, roll = dir
    inclination = np.pi/2 - pitch
    azimuth = yaw

    # Calculate the x, y, z coordinates
    x = np.sin(inclination) * np.cos(azimuth)
    y = np.sin(inclination) * np.sin(azimuth)
    z = np.cos(inclination)

    return (x, y, z)

def dir_of_unit_sphere(loc):
    x, y, z = loc 
    
    # Calculate the inclination and azimuth angles
    inclination = np.arccos(z)
    azimuth = np.arctan2(y, x)

    # Calculate the pitch, roll, and yaw angles
    pitch = np.pi/2 - inclination
    roll = np.arctan2(np.sin(azimuth)*np.sin(inclination), np.cos(azimuth)*np.sin(inclination))
    yaw = azimuth

    return (pitch, roll, yaw)

def to_deg(dir):
    yaw, pitch, roll = dir
    return (math.degrees(yaw), math.degrees(pitch), math.degrees(roll))

def to_rad(dir):
    yaw, pitch, roll = dir
    return (math.radians(yaw), math.radians(pitch), math.radians(roll))


def xform(loc, dir, rotation):
    dir = to_rad(dir)
    rotation = to_rad(rotation)
    
    x, y, z = loc
    yaw, pitch, roll = rotation
    # Create the rotation matrix
    Rx = np.array([[1, 0, 0],
                [0, np.cos(roll), -np.sin(roll)],
                [0, np.sin(roll), np.cos(roll)]])
    Ry = np.array([[np.cos(pitch), 0, np.sin(pitch)],
                [0, 1, 0],
                [-np.sin(pitch), 0, np.cos(pitch)]])
    Rz = np.array([[np.cos(yaw), -np.sin(yaw), 0],
                [np.sin(yaw), np.cos(yaw), 0],
                [0, 0, 1]])
    R = Rz.dot(Ry.dot(Rx))

    # Define the input vector
    v = np.array([x, y, z])

    # Apply the rotation to the vector
    v_rotated = R.dot(v)

    # Print the rotated vector
    print("Rotated point:", v_rotated)

    dp = unit_sphere(dir)
    vd = np.array([dir[0], dir[1], dir[2]])
    vd_rotated = R.dot(vd)
    rdir = dir_of_unit_sphere(vd_rotated)

    print("Rotated dir:", to_deg(rdir))


print(xform((0, 0, 1), (90, 0, 45), (0, 0, 90)))
print(unit_sphere((0.5, 0.3, 1.2)))
print(dir_of_unit_sphere(unit_sphere((0.5, 0.3, 1.2))))