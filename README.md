# Macro Tool

Macro Tool is a desktop image-recognition macro tool built with Python.

Instead of replaying fixed coordinates and delays, it watches a selected screen region and runs an action when a configured image appears.

```text
When a specified image appears inside a specified screen region,
click the matched target.
```

This project is being developed both as a practical personal tool and as a portfolio project. The codebase is intentionally kept small, readable, and easy to extend.

## Status

v0.1 is in active development.

Current implementation includes:

- PySide6 desktop GUI
- JSON rule loading and saving
- Rule add, edit, and delete
- Screen region selection
- Multi-monitor region support
- Relative image paths in `rules.json`
- OpenCV template matching
- Japanese filename support for template images
- PyAutoGUI screenshot capture and mouse click execution
- Cooldown-based repeated click prevention
- Test detection without clicking
- Timestamped runtime logs

## Demo

The GIF below shows Macro Tool being used to detect and click an item that appears at random positions in another desktop application.

![Macro Tool demo](docs/assets/demo.gif)

The footage is used only as an example target application. Macro Tool itself is a general-purpose image-recognition macro tool and is not tied to a specific game.

## Screenshots

Main window:

![Main window](docs/assets/home.png)

Rule editor:

![Rule editor](docs/assets/rule.png)

Runtime log:

![Runtime log](docs/assets/execution.png)

## Concept

Traditional macro tools often rely on:

- fixed coordinates
- delays
- repeated loops

Macro Tool uses rule-based image detection instead:

- each rule has a template image
- each rule has a required search region
- each rule has a confidence threshold
- each rule has a cooldown
- when the image is found, the configured click action runs

Search regions are required in v0.1 to reduce false positives and keep detection fast.

## Tech Stack

- Python 3.11+
- PySide6
- PyAutoGUI
- OpenCV
- NumPy
- JSON
- pytest
- PyInstaller planned for executable packaging

## Quick Start

Install dependencies:

```bash
pip install -e .[dev]
```

Run the application:

```bash
python -m app.main
```

Run tests:

```bash
python -m pytest
```

## Basic Usage

1. Click `Add` to create a rule.
2. Set a rule name.
3. Choose a detection image.
4. Use `Select` to choose the search region.
5. Adjust confidence and cooldown.
6. Save the rule.
7. Use `Test Detection` to verify matching without clicking.
8. Click `Start` to run the macro loop.
9. Click `Stop` to stop execution.

## Rule Example

```json
{
  "enabled": true,
  "name": "Click item",
  "image": "image/item.png",
  "region": {
    "x": 100,
    "y": 200,
    "width": 300,
    "height": 120
  },
  "confidence": 0.85,
  "action": {
    "type": "click",
    "button": "left",
    "offset": {
      "x": 0,
      "y": 0
    }
  },
  "cooldown": 1.5
}
```

## Project Structure

```text
app/
  main.py
  models.py
  storage.py
  screenshot.py
  detector.py
  actions.py
  runner.py
  system.py
  rule_operations.py
  ui/
    main_window.py
    rule_editor.py
    region_selector.py
tests/
docs/
```

Main responsibility split:

- `models`: rule data structures and validation
- `storage`: JSON loading and saving
- `screenshot`: screenshot capture and virtual screen origin handling
- `detector`: OpenCV template matching
- `actions`: mouse action execution
- `runner`: macro execution loop and cooldown handling
- `ui`: PySide6 screens and user interaction

## Design Documents

- [UI design](docs/design.md)
- [Rule schema](docs/rule_schema.md)
- [Architecture](docs/architecture.md)

## v0.1 Scope

In scope:

- image-based click rules
- required search regions
- rule editing GUI
- region selection GUI
- JSON persistence
- test detection
- cooldown
- basic execution logs

Not planned for v0.1:

- coordinate-only macro recording
- delay-based step execution
- multiple actions per rule
- conditional branching
- keyboard actions
- OCR
- scheduling
- plugin system

## Notes

- Template image paths are saved relative to `rules.json` when possible.
- Negative region coordinates are allowed for multi-monitor setups.
- The click action moves the mouse to the target, clicks, and then returns the cursor to its original position.
- Some target applications may handle simulated mouse input differently from normal desktop applications.
