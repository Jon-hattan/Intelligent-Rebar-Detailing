# 🧱 Slab Reinforcement Detailing

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

