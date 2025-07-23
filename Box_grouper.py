
from collections import defaultdict

def group_boxes_by_vertical_and_void_overlap(boxes, void_boxes, y_threshold=20):
    groups = defaultdict(list)
    group_id = 0

    # Step 1: Group boxes by vertical overlap
    vertical_groups = []
    for idx, box in enumerate(boxes):
        min_y = min(pt[1] for pt in box)
        max_y = max(pt[1] for pt in box)
        assigned = False
        for group in vertical_groups:
            g_min_y, g_max_y = group['range']
            if abs(min_y - g_min_y) <= y_threshold or abs(max_y - g_max_y) <= y_threshold or (min_y <= g_max_y and max_y >= g_min_y):
                group['boxes'].append((idx + 1, box))
                group['range'] = (min(min_y, g_min_y), max(max_y, g_max_y))
                assigned = True
                break
        if not assigned:
            vertical_groups.append({'range': (min_y, max_y), 'boxes': [(idx + 1, box)]})

    # Step 2: Split each vertical group based on relevant void box overlap
    for group in vertical_groups:
        g_min_y, g_max_y = group['range']
        for idx, box in group['boxes']:
            x_min = min(pt[0] for pt in box)
            x_max = max(pt[0] for pt in box)
            y_min = min(pt[1] for pt in box)
            y_max = max(pt[1] for pt in box)

            relevant_voids = [vb for vb in void_boxes if not (vb[3] < y_min or vb[1] > y_max)]

            if not relevant_voids:
                groups[group_id].append((idx, box))
            else:
                assigned = False
                for vb in relevant_voids:
                    if x_max < vb[0]:
                        groups[group_id + 1].append((idx, box))
                        assigned = True
                        break
                    elif x_min > vb[2]:
                        groups[group_id + 2].append((idx, box))
                        assigned = True
                        break
                if not assigned:
                    groups[group_id + 3].append((idx, box))
        group_id += 4

    return groups
