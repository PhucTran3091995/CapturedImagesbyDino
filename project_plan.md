# Project Plan: Dino Capture App Restructuring

## Overview
Restructure the capture workflow and PDF report generation to strictly follow the user's new requirements: 4 categories, 8 images per category, and specific PDF formatting with static NG examples.

## Tasks

### 1. Update Core Logic & UI (`gui/main_window.py`)
- [x] Update `qc_categories` to the 4 new Vietnamese categories.
- [x] Change total image count to 32 (4 items * 8 images).
- [x] Update UI list to display 8 image slots per category (likely 2 rows of 4 for better visibility).
- [x] Verify capture logic handles the new indexing correctly.

### 2. Update PDF Generation (`core/pdf_generator.py`)
- [x] Refactor the PDF header to match the screenshot (Socket Infor, Inspector(IQC), etc.).
- [x] Define the new table structure:
    - Columns: Dept (3 sub-cols merged), Item, Criteria, NG Example, Inspection Point (8 cells), Result, Note.
- [x] Implement logic to display the specific static images for "NG Example" column for each row.
    - `Linh kiện của adapter` -> `Adapter Components.png`
    - `Bụi bẩn` -> `Foreign material.png`
    - `Các chân tiếp xúc của socket` -> `Pin.png`
    - `Các điểm tiếp nối` -> `Pad.png`
- [x] Map the 8 captured images to the "Inspection Point" columns.
- [x] Ensure formatting (fonts, borders, spans) matches the reference image as closely as possible.

### 3. Verification
- [x] Code review of changes.
- [x] Ensure paths to 'pdf image' are correct.
