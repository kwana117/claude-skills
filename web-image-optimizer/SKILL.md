---
name: web-image-optimizer
description: Optimize images for web use - convert to JPG, rename sequentially, resize (horizontal max 1250px width, vertical max 1250px height), and compress to ~300KB. Use this skill whenever the user wants to process, optimize, compress, resize, or prepare images/photos for a website, even if they just say "optimize these photos" or "prepare images for web".
---

# Web Image Optimizer

Automates the full pipeline of preparing images for web use: convert, rename, resize, and compress.

## Prerequisites

- **ImageMagick** must be installed (`brew install imagemagick` on macOS)
- Verify with: `which magick`

## The Pipeline

When the user asks to optimize images, follow these steps in order:

### 1. Scan the source folder

List all images and show a summary:
- Total number of images found
- Formats present (JPG, HEIC, PNG, TIFF, etc.)
- Total size
- Size range (smallest to largest)

Supported formats: `.jpg`, `.jpeg`, `.png`, `.heic`, `.heif`, `.tiff`, `.tif`, `.webp`, `.bmp`

### 2. Ask the user for preferences (if not already provided)

- **Source folder**: where the original images are
- **Naming prefix**: e.g., `fotos-joana-ferreira` → produces `fotos-joana-ferreira-1.jpg`, `fotos-joana-ferreira-2.jpg`, etc.
- **Starting number**: default is 1, but if the user already has photos numbered 1-22, start at 23

### 3. Create output folder

Never modify originals. Create a sibling folder named `<source>-optimized/`.

Example: `more-photos/` → `more-photos-optimized/`

### 4. Process each image

For each image, run this ImageMagick command:

```bash
magick "<input>" -auto-orient -strip -resize <resize> -quality <quality> -sampling-factor 4:2:0 -colorspace sRGB "<output>.jpg"
```

**Resize rules:**
- If width > height (horizontal): `-resize 1250x` (max 1250px width, height scales proportionally)
- If height >= width (vertical): `-resize x1250` (max 1250px height, width scales proportionally)
- If already within limits: no resize needed

**Compression strategy:**
- Start at quality 82
- Check file size after conversion
- If > 400KB, reduce quality by 5 and re-convert
- Repeat until ≤ 400KB or quality reaches 50 (never go below 50)
- Target is ~300KB per image

**Flags explained:**
- `-auto-orient`: fix rotation from EXIF data
- `-strip`: remove all metadata (EXIF, GPS, etc.) — reduces size and improves privacy
- `-sampling-factor 4:2:0`: chroma subsampling, standard for web JPEGs
- `-colorspace sRGB`: ensure consistent color across browsers

### 5. Show results

After processing, display a summary table:

```
Original Name              → New Name                    Size    Reduction
Cópia de IMG_8242.jpg      → fotos-joana-ferreira-1.jpg  285KB   -99%
IMG_5660.HEIC              → fotos-joana-ferreira-2.jpg  198KB   -87%
...
```

And totals:
- Images processed: X / Y
- Total size before: XXX MB
- Total size after: XX MB
- Overall reduction: XX%

### 6. Offer next steps

- Ask if the user wants to move the optimized images to a specific folder
- Ask if the originals can be deleted (never delete without explicit confirmation)
- If images from other folders also need processing, offer to repeat

## Important Notes

- Write a temporary bash script (e.g., `_process.sh`) to do the processing, then delete it after. This avoids quoting issues with inline bash loops.
- Use `#!/bin/bash` (not zsh) — zsh on macOS lacks `mapfile`. Use `while IFS= read -r -d '' f` with `find -print0` to handle filenames with spaces, accents, or special characters safely.
- Always quote file paths with double quotes — filenames may have spaces, accents (e.g., "Cópia de"), or leading spaces.
- Always show progress: `[1/33] Processing image.jpg...`
- If an image fails, log the error and continue with the next one.
- Sort input files alphabetically for consistent numbering.
- After processing, offer to move originals to a `_unprocessed/` subfolder inside the source directory.

## Script Template

Use this as a base when generating the processing script:

```bash
#!/bin/bash
set -euo pipefail

SOURCE_DIR="<source>"
OUTPUT_DIR="<source>-optimized"
PREFIX="<prefix>"

mkdir -p "$OUTPUT_DIR"

counter=<start_number>
total_original=0
total_final=0
errors=0

files=()
while IFS= read -r -d '' f; do
    files+=("$f")
done < <(find "$SOURCE_DIR" -maxdepth 1 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.heic" -o -iname "*.heif" -o -iname "*.tiff" -o -iname "*.webp" -o -iname "*.bmp" \) -print0 | sort -z)

TOTAL=${#files[@]}
echo "Processing $TOTAL images..."

for img in "${files[@]}"; do
    basename_img=$(basename "$img")
    new_name="${PREFIX}-${counter}.jpg"
    output_path="$OUTPUT_DIR/$new_name"

    original_size=$(stat -f%z "$img")
    original_kb=$((original_size / 1024))
    total_original=$((total_original + original_kb))

    dims=$(magick identify -format "%wx%h" "$img" 2>/dev/null || echo "0x0")
    width="${dims%%x*}"
    height="${dims##*x}"

    if [ "$width" -gt "$height" ]; then
        resize_opt="-resize 1250x"
    else
        resize_opt="-resize x1250"
    fi

    quality=82
    if ! magick "$img" -auto-orient -strip $resize_opt -quality $quality \
        -sampling-factor 4:2:0 -colorspace sRGB "$output_path" 2>/dev/null; then
        printf "[%2d/%d] %-45s  ERRO\n" "$counter" "$TOTAL" "$basename_img"
        errors=$((errors + 1))
        counter=$((counter + 1))
        continue
    fi

    current_kb=$(( $(stat -f%z "$output_path") / 1024 ))

    while [ "$current_kb" -gt 400 ] && [ "$quality" -gt 50 ]; do
        quality=$((quality - 5))
        magick "$img" -auto-orient -strip $resize_opt -quality $quality \
            -sampling-factor 4:2:0 -colorspace sRGB "$output_path" 2>/dev/null
        current_kb=$(( $(stat -f%z "$output_path") / 1024 ))
    done

    total_final=$((total_final + current_kb))
    reduction=$(( (original_kb - current_kb) * 100 / original_kb ))
    final_dims=$(magick identify -format "%wx%h" "$output_path" 2>/dev/null)

    printf "[%2d/%d] %-45s %5dKB -> %-40s %4dKB (q%d, %s, -%d%%)\n" \
        "$counter" "$TOTAL" "$basename_img" "$original_kb" "$new_name" \
        "$current_kb" "$quality" "$final_dims" "$reduction"

    counter=$((counter + 1))
done

echo ""
echo "=== RESUMO ==="
echo "Processadas: $((counter - 1 - errors)) / $TOTAL"
[ "$errors" -gt 0 ] && echo "Erros: $errors"
echo "Antes:  $((total_original / 1024)) MB"
echo "Depois: $((total_final / 1024)) MB"
echo "Reducao: $(( (total_original - total_final) * 100 / total_original ))%"
```
