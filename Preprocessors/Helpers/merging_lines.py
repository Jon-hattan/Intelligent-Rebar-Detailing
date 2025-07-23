import numpy as np


def angle_between_lines(l1, l2):
    def unit_vector(p1, p2):
        v = np.array([p2[0] - p1[0], p2[1] - p1[1]])
        norm = np.linalg.norm(v)
        return v / norm if norm > 0 else v

    u1 = unit_vector((l1[0], l1[1]), (l1[2], l1[3]))
    u2 = unit_vector((l2[0], l2[1]), (l2[2], l2[3]))
    dot = np.clip(np.dot(u1, u2), -1.0, 1.0)
    return np.degrees(np.arccos(dot))

def lines_are_mergeable(l1, l2, angle_thresh=5, dist_thresh=20):
    angle = angle_between_lines(l1, l2)
    if angle > angle_thresh:
        return False

    points1 = [(l1[0], l1[1]), (l1[2], l1[3])]
    points2 = [(l2[0], l2[1]), (l2[2], l2[3])]
    dists = [np.linalg.norm(np.subtract(p1, p2)) for p1 in points1 for p2 in points2]
    return min(dists) < dist_thresh

def merge_line_group(group):
    points = []
    for x1, y1, x2, y2 in group:
        points.append((x1, y1))
        points.append((x2, y2))
    # Fit bounding box between all endpoints
    [x1, y1] = min(points, key=lambda p: (p[0], p[1]))
    [x2, y2] = max(points, key=lambda p: (p[0], p[1]))
    return [x1, y1, x2, y2]

def efficient_merge_lines(lines, angle_thresh=5, dist_thresh=20):
    used = [False] * len(lines)
    merged = []

    for i in range(len(lines)):
        if used[i]:
            continue
        group = [lines[i][0]]
        used[i] = True
        for j in range(i+1, len(lines)):
            if not used[j] and lines_are_mergeable(lines[i][0], lines[j][0], angle_thresh, dist_thresh):
                group.append(lines[j][0])
                used[j] = True
        merged.append(merge_line_group(group))
    return merged


def are_colinear_and_touching(l1, l2, angle_thresh=5, dist_thresh=10):
    def angle(line):
        x1, y1, x2, y2 = line
        return np.degrees(np.arctan2(y2 - y1, x2 - x1)) % 180
    
    angle1 = angle(l1)
    angle2 = angle(l2)
    if abs(angle1 - angle2) > angle_thresh:
        return False

    # Check if any endpoints are close
    p1 = [(l1[0], l1[1]), (l1[2], l1[3])]
    p2 = [(l2[0], l2[1]), (l2[2], l2[3])]
    for a in p1:
        for b in p2:
            if np.linalg.norm(np.subtract(a, b)) < dist_thresh:
                return True
    return False

def merge_lines_collinear(l1, l2):
    points = [(l1[0], l1[1]), (l1[2], l1[3]), (l2[0], l2[1]), (l2[2], l2[3])]
    
    # Sort by projected distance along the line direction
    line_vec = np.array([l1[2] - l1[0], l1[3] - l1[1]])
    line_unit = line_vec / np.linalg.norm(line_vec)
    
    projections = [np.dot(np.subtract(pt, (l1[0], l1[1])), line_unit) for pt in points]
    idx_min = np.argmin(projections)
    idx_max = np.argmax(projections)
    return [*points[idx_min], *points[idx_max]]

def merge_all_colinear_lines(lines, angle_thresh=1, dist_thresh=20):
    merged = []
    used = [False] * len(lines)
    
    for i in range(len(lines)):
        if used[i]:
            continue
        group = [lines[i]]
        used[i] = True
        for j in range(i+1, len(lines)):
            if not used[j] and are_colinear_and_touching(lines[i], lines[j], angle_thresh, dist_thresh):
                group.append(lines[j])
                used[j] = True
        # Merge all lines in the group into one
        current = group[0]
        for l in group[1:]:
            current = merge_lines_collinear(current, l)
        merged.append(current)
    return merged