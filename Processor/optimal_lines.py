import numpy as np
from collections import defaultdict


def find_optimal_lines_horizontal(group, Y_OFFSET, X_OVERLAP, x_rightbound, x_leftbound, x_min, x_max, MAX_LEN):
    group_rectangles = [box for _, box in group] #get boxes

    
    min_x_value_forGroup = int(min(min(x1, x2) for x1, _, x2, _ in group_rectangles))  # smallest x
    max_x_value_forGroup = int(max(max(x1, x2) for x1, _, x2, _ in group_rectangles))  # largest x

    min_y_value_forGroup = int(min(min(y1, y2) for _, y1, _, y2 in group_rectangles))  # smallest y
    max_y_value_forGroup = int(max(max(y1, y2) for _, y1, _, y2 in group_rectangles))  # largest y


    #if it is not the first box in the row, the line optimisation starts at the min x value, instead of the edge of the building
    if abs(min_x_value_forGroup - x_min) > 30:
            x_leftbound = min_x_value_forGroup
    #if it is not the last box in the row, the line optimisation ends at the max x value, instead of the edge of the building
    if abs(max_x_value_forGroup - x_max) > 30:
            x_rightbound = max_x_value_forGroup

    # Compute the mean y-position of each rectangle
    
    y_values = [y for _, y1, _, y2 in group_rectangles for y in (y1, y2)]
    middle_y = (min(y_values) + max(y_values)) // 2


    # Compute the center x-position of each rectangle
    centers = sorted([int((x1 + x2) / 2) for x1, y1, x2, y2 in group_rectangles])

    #generate all valid segments
    split_candidates = [x_leftbound] + centers + [x_rightbound]
    segments = []

    for i in range(len(split_candidates) - 1):
        x1 = split_candidates[i]
        for j in range(i + 1, len(split_candidates)):
            x2 = split_candidates[j]

            #check for load direction switch --> find out if load changes direction. indexing must -1 because split_candidates has extra element in front
            if j <= 1 or j >= len(split_candidates) - 1 or len(split_candidates) != 3:
                direction_switch = False
            else:
                direction1 = abs(group_rectangles[j-1][2] - group_rectangles[j-1][0]) > abs(group_rectangles[j-1][3] - group_rectangles[j-1][1])
                direction2 = abs(group_rectangles[j-2][2] - group_rectangles[j-2][0]) > abs(group_rectangles[j-2][3] - group_rectangles[j-2][1])
                direction_switch = (direction1 != direction2)

            if x2 - x1 > MAX_LEN:
                break
            else:
                segments.append((x1, x2))

            if direction_switch:
                break

            


    #dynamic programming for optimal splits. MAXIMISES THE SHORTEST LINE SEGMENT.
    dp = defaultdict(lambda: (-1, []))  # maps end_x to (min_segment_length, path)
    dp[x_leftbound] = (float('inf'), [x_leftbound])

    for x1, x2 in segments:
        if x1 in dp:
            min_len, path = dp[x1]
            new_min = min(min_len, x2 - x1) #minimum of the new segment and previous minimum segment
            if new_min > dp[x2][0]:
                dp[x2] = (new_min, path + [x2])

    _, best_path = dp[x_rightbound]

    lines = []
    arrows = []
    circles = []
    for i in range(len(best_path) - 1):
        #ADD LINES
        #ensure that there is a bit of x-axis overlap between lines.
        x1 = best_path[i] - X_OVERLAP if best_path[i] != x_leftbound else best_path[i]
        x2 = best_path[i + 1] + X_OVERLAP if best_path[i + 1] != x_rightbound else best_path[i + 1] 

        #ensure that there is a y-offset between lines.
        y = middle_y + ((-1) ** i) * Y_OFFSET

        lines.append(((x1, y), (x2, y)))


        #ADD PERPENDICULAR ARROWS
        # Midpoint of the line
        mid_x = 0.5 * (x1 + x2)

        # Arrow spans full vertical extent of the group
        arrows.append(((mid_x, min_y_value_forGroup), (mid_x, max_y_value_forGroup)))


        # Circles in the center of the arrows (x, y, line_width)
        circles.append((mid_x, y, min_y_value_forGroup, max_y_value_forGroup))


    return lines, arrows, circles



def find_optimal_lines_vertical(group, X_OFFSET, Y_OVERLAP, y_topbound, y_bottombound, y_min, y_max, MAX_LEN):
    group_rectangles = [box for _, box in group]

    min_y_value_forGroup = int(min(min(y1, y2) for x1, y1, x2, y2 in group_rectangles))
    max_y_value_forGroup = int(max(max(y1, y2) for x1, y1, x2, y2 in group_rectangles))
    min_x_value_forGroup = int(min(min(x1, x2) for x1, y1, x2, y2 in group_rectangles))
    max_x_value_forGroup = int(max(max(x1, x2) for x1, y1, x2, y2 in group_rectangles))

    if abs(min_y_value_forGroup - y_min) > 30:
        y_topbound = min_y_value_forGroup
    if abs(max_y_value_forGroup - y_max) > 30:
        y_bottombound = max_y_value_forGroup


    x_values = [x for x1, _, x2, _ in group_rectangles for x in (x1, x2)]
    middle_x = (min(x_values) + max(x_values)) // 2

    centers = sorted([int((y1 + y2) / 2) for x1, y1, x2, y2 in group_rectangles])
    split_candidates = [y_topbound] + centers + [y_bottombound]

    segments = []
    for i in range(len(split_candidates) - 1):
        y1 = split_candidates[i]
        for j in range(i + 1, len(split_candidates)):
            y2 = split_candidates[j]

            #check for load direction switch --> find out if load changes direction. indexing must -1 because split_candidates has extra element in front
            if j <= 1 or j >= len(split_candidates) - 1 or len(split_candidates) != 3:
                direction_switch = False
            else:
                direction1 = abs(group_rectangles[j-1][2] - group_rectangles[j-1][0]) > abs(group_rectangles[j-1][3] - group_rectangles[j-1][1])
                direction2 = abs(group_rectangles[j-2][2] - group_rectangles[j-2][0]) > abs(group_rectangles[j-2][3] - group_rectangles[j-2][1])
                direction_switch = (direction1 != direction2)

            if y2 - y1 > MAX_LEN:
                break
            else:
                segments.append((y1, y2))

            if direction_switch:
                break

    dp = defaultdict(lambda: (-1, []))
    dp[y_topbound] = (float('inf'), [y_topbound])

    for y1, y2 in segments:
        if y1 in dp:
            min_len, path = dp[y1]
            new_min = min(min_len, y2 - y1)
            if new_min > dp[y2][0]:
                dp[y2] = (new_min, path + [y2])

    _, best_path = dp[y_bottombound]

    lines = []
    arrows = []
    circles = []
    for i in range(len(best_path) - 1):
        y1 = best_path[i] - Y_OVERLAP if best_path[i] != y_topbound else best_path[i]
        y2 = best_path[i + 1] + Y_OVERLAP if best_path[i + 1] != y_bottombound else best_path[i + 1]

        x = middle_x + ((-1) ** i) * X_OFFSET
        lines.append(((x, y1), (x, y2)))

        mid_y = 0.5 * (y1 + y2)
        arrows.append(((min_x_value_forGroup, mid_y), (max_x_value_forGroup, mid_y)))

        circles.append((x, mid_y, min_x_value_forGroup, max_x_value_forGroup))

    return lines, arrows, circles
