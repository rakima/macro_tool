# Macro Tool

[日本語版 README](README.ja.md)

Macro Tool is a desktop image-recognition macro tool built with Python.

Instead of replaying fixed coordinates and delays, it watches a selected screen region and runs an action when a configured image appears.

```text
When a specified image appears inside a specified screen region,
click the matched target.
```

This project is being developed both as a practical personal tool and as a portfolio project. The codebase is intentionally kept small, readable, and easy to extend.

## Status

v0.1 is in active development. Packaged executables are alpha-quality experimental builds for prototype demos.

Current implementation includes:

- PySide6 desktop GUI
- JSON rule loading and saving
- Rule add, edit, and delete
- Screen region selection
- Click position selection on the template image
- Multi-monitor region support
- Relative image paths in `rules.json`
- OpenCV template matching
- Transparent PNG mask support for ignored template areas
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

Click position selector:

![Click position selector](docs/assets/select_clicked_position.png)

Mask editor:

![Mask editor](docs/assets/editmask.png)

Masked template image:

![Masked template image](docs/assets/editmask_after.png)

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

## Build

PyInstaller is included in the development dependencies.

Build a Windows demo executable:

```powershell
.\scripts\build_windows.ps1
```

The executable is created at:

```text
dist/MacroTool/MacroTool.exe
```

The packaged executable starts the GUI by default. Packaged builds are currently experimental and intended for v0.1 prototype demos.

GitHub Releases can be created from tags such as `v0.1.0-alpha.1`. The release workflow builds the Windows package in CI and attaches a zip archive as a release asset.

## Basic Usage

1. Click `Add` to create a rule.
2. Set a rule name.
3. Choose a detection image.
4. Use `Select` to choose the search region.
5. Use `Edit Mask` when parts of the detection image should be ignored.
6. Use click offset `Select` to choose the click position on the template image.
7. Adjust confidence and cooldown.
8. Save the rule.
9. Use `Test Detection` to verify matching without clicking.
10. Click `Start` to run the macro loop.
11. Click `Stop` to stop execution.

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
- Transparent pixels in PNG template images are ignored during detection.
- `Edit Mask` saves a separate `*.masked.png` file and updates the rule image path.
- Negative region coordinates are allowed for multi-monitor setups.
- The click action moves the mouse to the target, clicks, and then returns the cursor to its original position.
- Some target applications may handle simulated mouse input differently from normal desktop applications.
- Do not run rule files from untrusted sources.
- When an enabled rule's search region overlaps the Macro Tool window, the app asks for confirmation before starting.

## Known Limitations

- Packaged builds are currently Windows-focused.
- The executable is unsigned, so Windows Defender or SmartScreen may show a warning.
- Some applications may ignore simulated mouse input or handle it differently from normal clicks.
- Rule files can trigger mouse actions, so only use rule files from trusted sources.
- Keyboard actions, OCR, scheduling, multiple actions per rule, and conditional branching are not supported in v0.1.
- Rule data is stored in `rules.json` next to the executable when using the packaged build.

## License

This project is licensed under the MIT License.
