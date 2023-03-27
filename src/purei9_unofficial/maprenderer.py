import matplotlib.pyplot as plt
import numpy as np
import gzip
import json

def transform(points, xya):
    translate = xya[0:2]
    angle = -1 * xya[2]
    R = np.array([[np.cos(angle), -np.sin(angle)],[np.sin(angle),np.cos(angle)]])
    
    #return np.matmul(points-translate, R)
    return np.matmul(R, (points-translate).T).T

def plot_map(map_data_gzip: bytes):
    map_data = json.loads(gzip.decompress(map_data_gzip))
    
    transform_ids = np.array([crumb["t"] for crumb in map_data['crumbs']])
    points = np.array([np.array(crumb['xy']) for crumb in map_data['crumbs']])
    
    transforms = {}
    for transform_data in map_data['transforms']:
        transforms[transform_data['t']] = np.array(transform_data['xya'])
    
    unique_transform_ids = np.unique(transform_ids)
    transformed_points = np.zeros(points.shape)
    for transform_id in unique_transform_ids:
        transformed_points[transform_ids==transform_id] = transform(points[transform_ids==transform_id], transforms[transform_id])
    
    #plt.scatter(transformed_points[:,0], transformed_points[:,1],s=150)
    plt.plot(transformed_points[:,0], transformed_points[:,1],linewidth=0.3)
    
    charger_pose = map_data["chargerPose"]
    charger_pose_transform = transforms[charger_pose['t']]
    charger_pos = np.array(charger_pose['xya'][0:2])
    charger_angle = charger_pose['xya'][2]
    charger_pos_transformed = transform(charger_pos, charger_pose_transform)
    charger_angle_transformed = charger_angle - charger_pose_transform[2]
    
    plt.scatter(charger_pos_transformed[0],charger_pos_transformed[1],marker=(3,0,90+charger_angle_transformed*180/np.pi),s=200)
    
    
    ax = plt.gca()
    ax.set_aspect('equal', adjustable='box')
    plt.show(block=True)