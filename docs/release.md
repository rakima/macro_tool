# Release Notes

## Release Policy

Macro Tool is currently in v0.1 alpha.

Releases are intended as prototype demo builds. They are useful for portfolio review and local testing, but they should not be treated as stable production builds yet.

## Version Naming

Use alpha tags while the v0.1 feature set is still being refined.

Examples:

```text
v0.1.0-alpha.1
v0.1.0-alpha.2
```

## Release Checklist

1. Run tests locally.

   ```powershell
   python -m pytest
   ```

2. Build locally when changing packaging behavior.

   ```powershell
   .\scripts\build_windows.ps1
   ```

3. Confirm the packaged app starts.

   ```text
   dist/MacroTool/MacroTool.exe
   ```

4. Update README screenshots or demo assets when the UI changes noticeably.

5. Create and push a version tag.

   ```powershell
   git tag v0.1.0-alpha.1
   git push origin v0.1.0-alpha.1
   ```

6. Confirm the GitHub Actions release workflow completed successfully.

## v0.1.0 Stable Candidate Checklist

Use this checklist before removing the alpha label from v0.1.0.

- Fresh application launch succeeds.
- Rule creation works.
- Detection image selection works.
- Search region selection works.
- Click position selection works.
- Mask editing creates a `*.masked.png` file.
- Rule saving writes `rules.json`.
- Saved rules load correctly after restarting the packaged app.
- Test Detection works without clicking.
- Start and Stop work.
- Cooldown prevents repeated triggering.
- Japanese filename template images load correctly.
- Multi-monitor regions, including negative coordinates, work.
- Missing or invalid images show a useful validation error.
- Fully transparent PNG templates are rejected.
- Rules overlapping the Macro Tool window show a confirmation before Start.
- README screenshots and demo assets match the current UI.
- GitHub Actions creates `MacroTool-windows.zip`.

## Release Asset

The release workflow creates a Windows zip archive:

```text
MacroTool-windows.zip
```

This archive contains the PyInstaller `dist/MacroTool` directory.

## Notes for Users

- This is an experimental alpha build.
- Windows Defender or SmartScreen may warn about unsigned executables.
- Rule data is stored in `rules.json` next to the executable when using the packaged build.
- Target applications may handle simulated mouse input differently.
