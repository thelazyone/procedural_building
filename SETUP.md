# Setup Guide

## Installation

### 1. Install the main library

From the project root:

```bash
pip install -e .
```

This installs the `procedural_building` library in development mode along with its core dependency (Shapely).

### 2. Install debug viewer dependencies

```bash
cd debug_viewer
pip install -r requirements.txt
```

This installs:
- pygame (for windowing and UI)
- PyOpenGL (for 3D rendering)
- pygame-gui (for UI widgets)

## Running the Debug Viewer

From the project root:

```bash
python -m debug_viewer
```

## Running Examples

```bash
python examples/simple_building.py
```

### Testing Changes

After modifying the core library, just run the debug viewer again (no reinstall needed thanks to `-e` flag):

```bash
python -m debug_viewer
```
