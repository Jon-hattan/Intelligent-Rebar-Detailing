# 🧱 Intelligent Rebar Detailing

A Python application that automates the analysis of structural floor plans and optimizes rebar detailing using computer vision, engineering rules, and an interactive GUI.

## Table of Contents
- [🚀 Overview](#---overview)
- [✨ Key Features](#--key-features)
- [🛠️ Tools Used](#----used-)
- [Demo Video:](#demo-video-)
- [📐 Rebar Detailing Rules & Logic](#---rebar-detailing-rules---logic)
- [Algorithm Overview](#algorithm-overview)
  * [🔍 Stage 1: Preprocessing](#---stage-1--preprocessing)
  * [🧠 Stage 2: Processing & Rebar Grouping](#---stage-2--processing---rebar-grouping)




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

<br>
<br>


## Algorithm Overview

### 🔍 Stage 1: Preprocessing

The preprocessing stage prepares the scanned structural diagram for rebar detailing by identifying slab regions, beams, and voids using computer vision techniques. This stage involves three key scripts: `boundingbox_detector2.py`, `void_box_detector.py` and `rectangle_subtraction.py`.

#### 1.1 Bounding Box Detection (`BoundingBox_detector2.py`)
- The diagram is analyzed using **OpenCV** to detect structural elements.
- **Beams** are identified as **grey or black rectangular regions**.
- **Slabs** are registered as **white rectangles enclosed within beams**.
- These slab and beam regions are extracted and passed on for further processing.

#### 1.2 Void Detection (`Void_box_detector.py`)
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
   

#### 1.3 Rectangle Subtraction & Slab Segmentation (`rectangle_subtraction.py`)
- **Subtracts void boxes** from slab regions to ensure rebars are not placed in openings.
- **Splits slabs into smaller rectangles**, either **horizontally or vertically**, to create zones of rebar continuity.
- This segmentation makes it easier for later processing to be done to optimize the arrangement of rebars.


This preprocessing stage ensures that only valid slab regions are considered for rebar detailing, and that voids boxes are excluded from reinforcement zones.
<br>


### 🧠 Stage 2: Processing & Rebar Grouping

After preprocessing, the slab regions are grouped and optimized for rebar continuity using spatial logic and dynamic programming.

#### 2.1 Slab Region Grouping (`Box_grouper2.py`)
- This script groups the **split slab rectangles** into logical zones for rebar continuity.
- Grouping behavior depends on the **rebar direction**:
  - **Horizontal rebars**: Group boxes **horizontally first**, then merge **vertically aligned groups**.
  - **Vertical rebars**: Group boxes **vertically first**, then merge **horizontally aligned groups**.
- Grouping constraints:
  - **Void boxes** between slabs prevent grouping, ensuring rebars do not pass through openings.
  - **Beams with parallel reinforcement** prevent grouping to avoid rebars running parallel to beam reinforcement.

This grouping logic ensures that rebar continuity respects structural boundaries and avoids conflicts with voids and beam reinforcement.

#### 2.2 Optimal Rebar Line Placement (`optimal_lines.py`)
- For each group, the algorithm computes the **optimal rebar layout** using a dynamic programming strategy that **maximizes the shortest segment length** (mini-max optimization).
  1. **Bounding Limits**: Determine slab boundaries and adjust start/end points based on proximity to building edges.
  2. **Segment Generation**:
     - Identify center points of rectangles.
     - Generate all valid rebar segments between these points.
     - Respect the maximum rebar length (`MAX_LEN`, typically 12m).
     - Detect and halt at **load direction switches** to preserve structural logic.
  3. **Dynamic Programming**:
     - Track the best path of segments using a cache.
     - Update paths only if the new minimum segment length improves the previous.
  4. **Output Generation**:
     - Draw rebar lines with slight overlaps (`X_OVERLAP` or `Y_OVERLAP`) for continuity.
     - Add perpendicular **arrows** to indicate load direction.
     - Place **circles** at midpoints for annotation and clarity.


This stage finalizes the rebar layout logic before annotation and export. From there, `Main_processor.py` will annotate the diagram and export.







