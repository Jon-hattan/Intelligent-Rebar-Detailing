import numpy as np
import math 

# Function to determine if a line is dotted
def is_dotted(img, line, transition_threshold, regularity_threshold):
    x1, y1, x2, y2 = line  # Unpack the coordinates of the line
    line_pixels = img[min(y1, y2):max(y1, y2), min(x1, x2):max(x1, x2)]
    dark_pixels = np.sum(line_pixels > 200)  # Counts dark pixels

    transitions = np.diff(line_pixels > 100).astype(np.int32)  # Calculate transition points (0->1 or 1->0)
    
    # Count number of transitions
    transition_count = np.sum(np.abs(transitions) > 0)
    
    # Ensure the frequency of transitions is approximately equal
    if transition_count > transition_threshold and np.std(np.diff(np.where(transitions != 0)[0])) < regularity_threshold:  # Check for regularity
        return "Is Dotted Line"
    
    if transition_count <= transition_threshold:
        return "Not Enough Transitions"
    
    if np.std(np.diff(np.where(transitions != 0)[0])) >= regularity_threshold:
        return "Lines too Irregular"


def calculate_angle(x1, y1, x2, y2):
    angle_rad = math.atan2(y2 - y1, x2 - x1)
    angle_deg = math.degrees(angle_rad)
    return angle_deg if angle_deg >= 0 else angle_deg + 180  # Ensure 0°-180°