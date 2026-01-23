# Task Plan: Add NG Example Column to Main Window

## Objective
Update `gui/main_window.py` to include an "NG Example" column in the main UI, displaying a static reference image for each inspection category, matching the PDF report structure.

## Context
- The current UI displays 4 categories vertically.
- Each category has a grid of 8 captured images.
- We need to add a reference "NG Example" image to each category.
- Reference images are located in the `pdf image` directory.

## Steps

### 1. Define Image Mapping
Create a dictionary or list mapping category indices to their respective "NG Example" image filenames:
- Index 0: `Adapter Components.png`
- Index 1: `Foreign material.png`
- Index 2: `Pin.png`
- Index 3: `Pad.png`

### 2. Update UI Layout (in `gui/main_window.py`)
Modify the loop in `init_ui` that creates category widgets:
- **Current:** `QGroupBox` -> `QGridLayout` containing 8 `ImageBox` widgets.
- **New:** 
    - `QGroupBox` -> `QHBoxLayout`
        - **Left Item:** "NG Example" Image (`QLabel` with `QPixmap`, scaled to a reasonable size, e.g., similar to `ImageBox` size).
        - **Right Item:** Container Widget -> `QGridLayout` containing the 8 `ImageBox` widgets.

### 3. Implement Image Loading
- Construct the absolute path to the `pdf image` folder.
- Load the image using `QPixmap`.
- Handle potential missing images gracefully (e.g., placeholder or empty).

## Verification
- Run the application.
- Verify that each of the 4 categories displays the correct NG Example image on the left.
- Verify that the image capture grid still functions correctly (2x4 grid).
- Ensure layout spacing and alignment look good ("WOW" factor - maybe add a border or label).
