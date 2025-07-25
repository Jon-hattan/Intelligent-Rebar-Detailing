import numpy as np
from collections import defaultdict


def find_optimal_lines(group, Y_OFFSET, X_OVERLAP, x_rightbound, x_leftbound, x_min, x_max, MAX_LEN):
    group_rectangles = [box for _, box in group] #get boxes

    
    min_x_value_forGroup = int(min(min(x1, x2) for x1, y1, x2, y2 in group_rectangles))  # smallest x
    max_x_value_forGroup = int(max(max(x1, x2) for x1, y1, x2, y2 in group_rectangles))  # largest x

    min_y_value_forGroup = int(min(min(y1, y2) for x1, y1, x2, y2 in group_rectangles))  # smallest y
    max_y_value_forGroup = int(max(max(y1, y2) for x1, y1, x2, y2 in group_rectangles))  # largest y


    #if it is not the first box in the row, the line optimisation starts at the min x value, instead of the edge of the building
    if abs(min_x_value_forGroup - x_min) > 30:
            x_leftbound = min_x_value_forGroup
    #if it is not the last box in the row, the line optimisation ends at the max x value, instead of the edge of the building
    if abs(max_x_value_forGroup - x_max) > 30:
            x_rightbound = max_x_value_forGroup

    # Compute the mean y-position of each rectangle
    y_positions = [((y1 + y2) / 2) for x1, y1, x2, y2 in group_rectangles]
    min_y = min(y_positions)  # Get minimum y-position

    # Compute the center x-position of each rectangle
    centers = sorted([int((x1 + x2) / 2) for x1, y1, x2, y2 in group_rectangles])

    #generate all valid segments
    split_candidates = [x_leftbound] + centers + [x_rightbound]
    segments = []
    for i in range(len(split_candidates) - 1):
        x1 = split_candidates[i]
        for j in range(i + 1, len(split_candidates)):
            x2 = split_candidates[j]
            if x2 - x1 <= MAX_LEN:
                segments.append((x1, x2))
            else:
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
    for i in range(len(best_path) - 1):
        #ADD LINES
        #ensure that there is a bit of x-axis overlap between lines.
        x1 = best_path[i] - X_OVERLAP if best_path[i] != x_leftbound else best_path[i]
        x2 = best_path[i + 1] + X_OVERLAP if best_path[i + 1] != x_rightbound else best_path[i + 1] 

        #ensure that there is a y-offset between lines.
        y = min_y + ((-1) ** i) * Y_OFFSET

        lines.append(((x1, y), (x2, y)))


        #ADD PERPENDICULAR ARROWS
        # Midpoint of the line
        mid_x = 0.5 * (x1 + x2)

        # Arrow spans full vertical extent of the group
        arrows.append(((mid_x, min_y_value_forGroup), (mid_x, max_y_value_forGroup)))


    return lines, arrows


