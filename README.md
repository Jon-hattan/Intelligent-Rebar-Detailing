# 🧱 Intelligent Rebar Detailing

A Python application that automates the analysis of structural floor plans and optimizes rebar detailing using computer vision, engineering rules, and an interactive GUI.

## 🚀 Overview

During my internship at **Jacobs International Consultants**, I observed that manually detailing slab reinforcement diagrams was a time-consuming and repetitive task, often taking civil engineering full-timers/interns several hours just to complete a single set. Ainnoway I'm doin that manually. I developed this tool to automate the process using **OpenCV** and **Python** and used **PyQt6** to create the GUI.

This application interprets scanned floor plan diagrams and generates optimized rebar placements in under **1 minute**, significantly improving both speed and accuracy in civil engineering workflows.

## ✨ Key Features

- 🧠 **Autonomous Diagram Analysis**  
  Uses image processing to detect slab geometry, load directions, and support spacing from floor plan diagrams.

- 🧮 **Optimized Reinforcement Placement**  
  Treats the layout problem as a **minimax optimization** task - maximizing the minimum rebar length to ensure efficient material usage and structural integrity. A dynamic programming solution is used to compute optimal paths for reinforcement placement.

- 🖥️ **Interactive GUI with PyQt6**  
  Provides a user-friendly interface for loading diagrams, calculating the scale factor (image to real-life), and exporting schedules.

- ⚡ **Massive Time Savings**  
  Reduces scheduling time from hours or days to just **under one minute per diagram set**.


## 🛠️ Used:
- **Python**
- **OpenCV** for image processing
- **PyQt6** for GUI development


## Demo Video:
https://github.com/user-attachments/assets/5cef2b24-e878-49fc-a382-38de04dd46bd  

<br>






## 📐 Rebar Detailing Rules & Logic

This automation tool follows a set of engineering rules to ensure that the generated rebar layouts are structurally sound, code-compliant, and optimized for constructability. Below are the core rules implemented:

### 1. Maximum Rebar Length
- Rebars **cannot exceed 12 meters** in length.
- Longer spans are automatically split using laps to comply with standard rebar sizes.

### 2. Lap Placement Strategy
- Laps are preferably placed **at the center of the slab** to ensure structural continuity and ease of construction.
- Laps **must not** be placed **inside beams**, as this can interfere with beam reinforcement and compromise structural integrity.

### 3. Beam Interaction Rules
- Rebars **can pass through beams** only if:
  - The **reinforcement direction in the slab is perpendicular** to the beam.
- This ensures proper anchorage and avoids congestion within the beam.

### 4. Void Boxes
- Rebars **cannot pass through void boxes**, which are denoted by dotted or dashed line boxes with a cross in the center.

### 5.  Load Direction-Based Splitting
- Rebars are **split (lapped)** when the **load direction changes**.
- Load direction is determined by:
  - The **red arrow** in the slab diagram, or
  - The **shortest side** of the slab (used as a heuristic when arrows are absent).

### 6. Mini-Max Optimization
- Rebar splitting is optimized to **maximize the shortest possible rebar**.
- This reduces material waste and simplifies on-site handling.
- The algorithm uses a **mini-max strategy** to balance lap locations and rebar lengths for efficient detailing.

---

These rules are embedded into the logic of the automation tool and guide the placement, splitting, and annotation of reinforcement bars across slab regions. The goal is to produce constructible, efficient, and code-compliant rebar layouts with minimal manual intervention.




## 🧪 Algorithm Overview

### 🔍 Stage 1: Preprocessing

The preprocessing stage prepares the scanned structural diagram for rebar detailing by identifying slab regions, beams, and voids using computer vision techniques. This stage involves two key scripts: `boundingbox_detector2.py` and `void_box_detector.py`.

#### 1.1 Bounding Box Detection (`boundingbox_detector2.py`)
- The diagram is analyzed using **OpenCV** to detect structural elements.
- **Beams** are identified as **grey or black rectangular regions**.
- **Slabs** are registered as **white rectangles enclosed within beams**.
- These slab regions are extracted and passed on for further processing.

#### 1.2 Void Detection (`void_box_detector.py`)
- This script detects **openings** (e.g., stairwells, ducts) where rebars should not be placed.
- It searches for **dotted or dashed line boxes** with a **dashed/dotted cross** inside them.
- The detection process includes:
  - **Contour filtering**: Only short contours are retained; long ones are discarded.
  - **First Hough Line Transform pass**:
    - Uses a **small `maxLineGap`** and **short `minLineLength`** to join fragmented dotted/dashed lines.
    - Checks for **pixel intensity transitions** to confirm dotted/dashed patterns.
  - **Second Hough Line Transform pass**:
    - Uses **relaxed parameters** to join lines missed in the first pass due to noise or overlapping details.
  - **Bounding box generation**:
    - Draws rectangles around detected voids.
    - Applies **morphological merging** to combine overlapping boxes caused by noise.
    - Adds logic to **snap rectangles** to the nearest horizontal/vertical dotted lines for improved accuracy.

This preprocessing stage ensures that only valid slab regions are considered for rebar detailing, and that voids are excluded from reinforcement zones.








