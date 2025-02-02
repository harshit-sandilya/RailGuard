import numpy as np


def angle_between_lines(p1, p2, p3, p4):
    # Compute direction vectors
    v1 = np.array([p2[0] - p1[0], p2[1] - p1[1]])
    v2 = np.array([p4[0] - p3[0], p4[1] - p3[1]])

    # Compute the dot product and magnitudes
    dot_product = np.dot(v1, v2)
    magnitude_v1 = np.linalg.norm(v1)
    magnitude_v2 = np.linalg.norm(v2)

    # Compute the cosine of the angle
    cos_theta = dot_product / (magnitude_v1 * magnitude_v2)

    # Compute the angle in radians and convert to degrees
    angle = np.arccos(np.clip(cos_theta, -1.0, 1.0))  # Clip to avoid numerical issues
    return np.degrees(angle)
