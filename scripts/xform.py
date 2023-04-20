import numpy as np
from math import sin, cos
import sys, json


def rotate_orientation(orientation, axis, degrees):
    pitch, yaw, roll = list(map(np.deg2rad, orientation))

    # Define the new axis and angle of rotation
    new_axis = np.array(axis)
    new_angle = np.deg2rad(degrees)

    # Convert existing Euler angles to a rotation matrix
    R = np.array([
        [cos(yaw)*cos(roll), cos(roll)*sin(yaw), -sin(roll)],
        [cos(pitch)*sin(roll)*sin(yaw)-cos(roll)*sin(pitch), 
        cos(pitch)*cos(roll)+sin(pitch)*sin(roll)*sin(yaw), 
        cos(yaw)*sin(pitch)],
        [sin(pitch)*sin(roll)+cos(pitch)*cos(roll)*sin(yaw), 
        cos(pitch)*sin(roll)*sin(yaw)-cos(roll)*sin(pitch), 
        cos(pitch)*cos(yaw)]
    ])

    # Define the new rotation matrix
    c = cos(new_angle)
    s = sin(new_angle)
    new_R = np.array([
        [new_axis[0]**2*(1-c)+c, new_axis[0]*new_axis[1]*(1-c)-new_axis[2]*s, 
        new_axis[0]*new_axis[2]*(1-c)+new_axis[1]*s],
        [new_axis[0]*new_axis[1]*(1-c)+new_axis[2]*s, new_axis[1]**2*(1-c)+c, 
        new_axis[1]*new_axis[2]*(1-c)-new_axis[0]*s],
        [new_axis[0]*new_axis[2]*(1-c)-new_axis[1]*s, 
        new_axis[1]*new_axis[2]*(1-c)+new_axis[0]*s, new_axis[2]**2*(1-c)+c]
    ])

    # Combine the two rotation matrices
    combined_R = np.matmul(new_R, R)

    # Convert the resulting rotation matrix back to Euler angles
    new_pitch = np.arcsin(-combined_R[1, 2])
    new_roll = np.arctan2(combined_R[1, 0], combined_R[1, 1])
    new_yaw = np.arctan2(combined_R[0, 2], combined_R[2, 2])

    # return the new Euler angles in degrees
    return list(map(np.rad2deg, [new_pitch, new_yaw, new_roll]))

def rotate_location(loc, axis, degrees):
    # Define the point to be rotated
    point = np.array(loc)

    # Define the axis of rotation (must be a unit vector)
    axis = np.array(axis)
    axis /= np.linalg.norm(axis)

    # Define the angle of rotation in radians
    angle = np.deg2rad(degrees)

    # Define the rotation matrix
    c = cos(angle)
    s = sin(angle)
    x, y, z = axis
    R = np.array([
        [c+x**2*(1-c), x*y*(1-c)-z*s, x*z*(1-c)+y*s],
        [x*y*(1-c)+z*s, c+y**2*(1-c), y*z*(1-c)-x*s],
        [x*z*(1-c)-y*s, y*z*(1-c)+x*s, c+z**2*(1-c)]
    ])

    # Apply the rotation to the point
    new_point = np.dot(R, point)

    # Print the new point coordinates
    return list(new_point)


def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def hack_orientation(p):
    dir = [ p['yaw'], p['pitch'], p['roll'] ]
    eprint(p["label"], dir)
    if dir == [ 0, 0, 90 ]:
        dir = [ 0, 0, -90 ]
    elif dir == [ 90, 0, 45 ]:
        dir = [ 0, 90, -45 ]
    # elif dir == [ 90, 0, -45 ]:
    #     dir = [ 0, 90, -45 ]
    p['yaw'] = dir[0]
    p['pitch'] = dir[1]
    p['roll'] = dir[2]

def xform():
    lxs = json.load(sys.stdin)
    
    # rotate 90 degrees around the z-axis, so ceiling becuase xz plane, y is height
    axis = [0.0, 0.0, 1.0]
    angle = -90.0
    
    for fixture in lxs['model']['fixtures']:
        p = fixture['parameters']
        
        loc = [ float(p['x']), float(p['y']), float(p['z']) ]
        loc = rotate_location(loc, axis, angle)
        p['x'] = loc[0]
        p['y'] = loc[1]
        p['z'] = loc[2]

        dir = [ float(p['pitch']), float(p['yaw']), float(p['roll']) ]
        # dir = rotate_orientation(dir, axis, angle)
        # p['pitch'] = dir[0]
        # p['yaw'] = dir[1]
        # p['roll'] = dir[2
        
        hack_orientation(p)

    print(json.dumps(lxs))

xform()
# print(json.dumps(json.load(sys.stdin)))

# print(rotate_orientation([0, 90, 0], [0, 0, 1], -90))
# print(rotate_location([0, 42.0, 0.0], [0, 0, 1.0], -90.0))
