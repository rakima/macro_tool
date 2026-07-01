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
