import numpy as np
from collections import defaultdict

def find_optimal_lines(group, Y_OFFSET, X_OVERLAP, x_max, x_min, MAX_LEN):
    group_rectangles = [box for _, box in group] #get boxes

    y_positions = [np.mean(box.reshape(4, 2), axis=0)[1] for box in group_rectangles]
    min_y = int(np.min(y_positions)) #get average y-position of boxes in the group


    centers = sorted([int(np.mean(box[:, 0])) for box in group_rectangles]) #centers of each box

    #generate all valid segments
    split_candidates = [x_min] + centers + [x_max]
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
    dp[x_min] = (float('inf'), [x_min])

    for x1, x2 in segments:
        if x1 in dp:
            min_len, path = dp[x1]
            new_min = min(min_len, x2 - x1) #minimum of the new segment and previous minimum segment
            if new_min > dp[x2][0]:
                dp[x2] = (new_min, path + [x2])

    _, best_path = dp[x_max]

    lines = []
    for i in range(len(best_path) - 1):
        #ensure that there is a bit of x-axis overlap between lines.
        x1 = best_path[i] - X_OVERLAP if best_path[i] != x_min else best_path[i]
        x2 = best_path[i + 1] + X_OVERLAP if best_path[i + 1] != x_max else best_path[i + 1] 

        #ensure that there is a y-offset between lines.
        y = min_y + ((-1) ** i) * Y_OFFSET

        lines.append(((x1, y), (x2, y)))

    return lines


