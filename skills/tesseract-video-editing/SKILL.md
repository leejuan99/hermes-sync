---
name: tesseract-video-editing
description: Use when user wants to edit video using Tesseract CLI.
version: 1.0.0
author: Hermes Agent
license: MIT
hermes:
  metadata:
    tags:
      - video
      - tesseract
      - editing
    related_skills:
      - tesseract-video
---

# Edit video with Tesseract

## When to Use
Use this skill when the user wants to edit existing footage into a finished video using the Tesseract CLI (e.g., cut clips, add titles, adjust audio, export for social media). It assumes the Tesseract CLI is installed via the tesseract-video skill.

Prerequisite: The `tesseract-video` skill must be installed (via `npx skills add mirage-hq/Tesseract`). This provides the Tesseract CLI (`tsrct`) and installation guidance.

## Always-on rules

- Verify the CLI version matches the pinned version in `tesseract-video/references/cli-version.txt` (currently 0.2.0) before starting.
- Use absolute paths for project and assets to avoid working‑directory confusion.
- Always preview a frame or filmstrip before exporting to catch mistakes early.
- Preserve the original `.tsrct` project file; never edit it as text.
- Export only after confirming edits via `tsrct project apply` and preview.

## Procedure

1. **Set up project root**
   Choose a folder for the project (e.g., `C:\Users\pc\Videos\myproject`).
   Inside it, run:
   ```sh
   tsrct project create --project project.tsrct
   ```
   This creates an empty `.tsrct` document with a default 3‑second, 1080×1920 composition named `main`.

2. **Import assets**
   For each footage clip, image, or audio file:
   ```sh
   tsrct project import-asset --kind video --file "C:\path\to\footage.mp4" --copy
   ```
   Replace `--kind` with `image` or `audio` as needed. The `--copy` flag packages the asset into the project.

3. **Inspect the project**
   Export the current JSON to review IDs and structure:
   ```sh
   tsrct project inspect --project project.tsrct --pretty > .tesseract-work/project.json
   ```
   Note the layer IDs you want to modify (video layer, etc.).

4. **Plan edits**
   Create an edits JSON array in `.tesseract-work/edits.json`. Example for a simple cut and title:
   ```json
   [
     { "action": "layer.trim", "layerId": "<video‑layer‑id>", "inMs": 0, "outMs": 5000 },
     { "action": "layer.create", "layerType": "text", "layerId": "title", "props": { "text": "My Title", "fontSize": 48, "fillColor": "#ffffff" } }
   ]
   ```
   Refer to the action schema via `tsrct project schema` for supported actions.

5. **Apply edits**
   ```sh
   tsrct project apply --project project.tsrct --actions .tesseract-work/edits.json
   ```

6. **Preview**
   Generate a filmstrip or frame to verify:
   ```sh
   tsrct filmstrip --project project.tsrct --start-ms 0 --duration-ms 5000 --interval-ms 500 --output Previews/filmstrip.png
   ```
   Or a single frame:
   ```sh
   tsrct preview --project project.tsrct --time 2500 --output Previews/frame.png
   ```

7. **Export**
   When satisfied, export the final video:
   ```sh
   tsrct export --project project.tsrct --output finished.mp4 --resolution 1080p --fps 30
   ```
   Adjust resolution, fps, or format (e.g., `--format prores`) as needed.

8. **Hand off**
   Deliver the `finished.mp4` and retain the `project.tsrct` for future revisions.

## Pitfalls

- **Missing assets** – If `import-asset` fails, verify the file path and that you have read permission.
- **Wrong aspect ratio** – The project canvas defaults to 1080×1920 (portrait). To change, edit the JSON via `project checkout`/`commit` before adding layers.
- **Export hangs** – Ensure a compatible Vulkan driver is available; on headless systems, install Mesa lavapipe for software rendering.
- **Audio not heard** – Import audio as an asset and place it on an Audio layer; export includes mix by default.
- **Unsupported action** – Check the schema (`tsrct project schema`) before inventing fields; only use actions listed there.

## References

- See `tesseract-video/references/local-operation.md` for full CLI lifecycle.
- See `tesseract-video/references/fx-authoring.md` for layer types and properties.
- See `tesseract-video/references/media-import.md` for asset‑kind details.
