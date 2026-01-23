# Task Plan: Fix UI Layout and Add Zoom to NG Example

## Objective
1. Fix the layout issue where image boxes stretch or arrange poorly when the window is maximized.
2. Add a feature to zoom in on the "NG Example" image when clicked.

## Steps

### 1. Update `gui/widgets.py`
- Create a `ClickableLabel` class (inherits `QLabel`) that emits a `clicked` signal.
- Create a `ZoomDialog` class (inherits `QDialog`) to show an image in a large scrollable area or fit-to-screen.
- Update `ImageBox`:
    - Set a fixed size or maximum size for the widget to prevent it from stretching awkwardly.
    - Current minimum is 80x60. Let's try setting a Fixed Size (e.g., 100x90) to maintain a neat grid.

### 2. Update `gui/main_window.py`
- Import `ClickableLabel` and `ZoomDialog` from `gui/widgets`.
- In `init_ui` loop:
    - Replace the standard `QLabel` for "NG Example" with `ClickableLabel`.
    - Connect its `clicked` signal to a new slot `show_ng_zoom(image_path)`.
    - Store the `image_path` in the label dynamically so it knows what to show.
- Layout adjustments:
    - Ensure the `grid_container` (right side) doesn't expand indefinitely. We can set `setSizePolicy` to `Fixed` or `Maximum`.
    - Or simply relying on the `ImageBox` fixed size will naturally limit the grid size.

## Verification
- Run the app.
- Maximize the window. Check if the grid squares remain a consistent, reasonable size (not stretched).
- Click the NG Example image. Check if a popup appears displaying the larger image.
