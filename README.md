# Macro Tool

Macro Tool is a planned desktop macro tool that detects images on the screen and runs actions such as mouse clicks.

This project replaces an older Go-based macro tool with a new Python GUI application. The goal is to build a tool that is practical for personal use while also keeping the codebase, UI, and documentation clear enough to present as a portfolio project.

## Status

This project is currently in the design phase.

Implementation has not started yet. The current focus is to define the UI, rule format, and application architecture before writing the first version of the Python application.

## Concept

Traditional macro tools often rely on fixed coordinates, delays, and repeated loops.

Macro Tool uses a different approach:

```text
When a specified image appears inside a specified screen region,
run the configured action.
```

For v0.1, every rule must have a search region. This keeps image detection faster and reduces false positives.

Instead of using per-step delays, rules use `cooldown` to prevent repeated triggering.

## Planned Tech Stack

- Python
- PySide6 for the GUI
- PyAutoGUI for screenshots and mouse actions
- OpenCV for image detection
- JSON for macro rule definitions
- PyInstaller for packaging as an executable

## v0.1 Scope

The first version focuses on a small but coherent image-detection macro workflow.

Planned screens:

- Main window
- Rule editor
- Region selector

Planned main window features:

- Start
- Stop
- Test detection
- Rule list
- Log output

Planned rule editor fields:

- Rule name
- Detection image
- Search region
- Confidence
- Action
- Cooldown

## Rule Example

```json
{
  "enabled": true,
  "name": "Click start button",
  "image": "images/start_button.png",
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

## Design Documents

- [UI design](docs/design.md)
- [Rule schema](docs/rule_schema.md)
- [Architecture](docs/architecture.md)

## Planned Architecture

The application is planned around small modules with clear responsibilities.

```text
app/
  main.py
  models.py
  storage.py
  detector.py
  actions.py
  runner.py
  ui/
    main_window.py
    rule_editor.py
    region_selector.py
```

Main responsibility split:

- `models`: rule data structures and validation
- `storage`: JSON loading and saving
- `detector`: image matching with OpenCV
- `actions`: mouse actions through PyAutoGUI
- `runner`: macro execution loop and cooldown handling
- `ui`: PySide6 screens and user interaction

## Not Planned for v0.1

- Coordinate-only macro recording
- Delay-based step execution
- Multiple actions per rule
- Conditional branching
- Keyboard actions
- OCR
- Scheduling
- Plugin system

## Development Policy

This project is intentionally developed in small steps.

The priority is not the fastest possible implementation. The priority is a maintainable design, understandable code, and a UI that feels useful in daily use.
