# Release checklist

1. Update `CHANGELOG.md`.
2. Check that the app starts from source:

   ```bat
   run.bat
   ```

3. Build the executable:

   ```bat
   build.bat
   ```

4. Test `dist\KnobMixer.exe` on Windows 10/11.
5. Push changes to GitHub.
6. Wait for the `Build Windows exe` workflow to pass.
7. Download the workflow artifact or attach it to a GitHub Release manually.

Recommended release assets:

```text
KnobMixer.exe
README.md
LICENSE
```
