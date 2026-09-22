"""Normalize supported original documents without reconstructing their contents."""
import io
import warnings
from PIL import Image, ImageOps
import pymupdf

VISUAL_FORMATS = {"pdf", "png", "jpg", "jpeg", "webp"}
MAX_BYTES = 25 * 1024 * 1024
MAX_PAGES = 30


def merge_sources(sources):
    """Return one original-content PDF and provenance for each page, in upload order."""
    if not sources or sum(len(data) for _, data in sources) > MAX_BYTES:
        raise ValueError("Upload up to 25 MB in total.")
    page_names = []
    with pymupdf.open() as merged:
        for filename, data in sources:
            ext = filename.rsplit(".", 1)[-1].lower()
            if ext not in VISUAL_FORMATS:
                raise ValueError("Multiple-file imports support PDF, JPG, PNG and WebP only.")
            if ext == "pdf":
                with pymupdf.open(stream=data, filetype="pdf") as original:
                    if original.needs_pass:
                        raise ValueError("Unlock password-protected PDFs before uploading.")
                    if len(merged) + len(original) > MAX_PAGES:
                        raise ValueError("Upload up to 30 pages or photos at a time.")
                    merged.insert_pdf(original)
                    page_names.extend(f"{filename} · page {i+1}" for i in range(len(original)))
            else:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", Image.DecompressionBombWarning)
                    with Image.open(io.BytesIO(data)) as original:
                        if getattr(original, "n_frames", 1) != 1:
                            raise ValueError("Animated or multi-frame images are not supported; upload still photos.")
                        if original.width * original.height > 40_000_000:
                            raise ValueError("Each photo must be 40 megapixels or smaller.")
                        image = ImageOps.exif_transpose(original).convert("RGBA")
                        background = Image.new("RGB", image.size, "white")
                        background.paste(image, mask=image.getchannel("A"))
                        buf = io.BytesIO(); background.save(buf, format="PNG")
                        # Preserve image pixels and orientation; place, do not redraw.
                        w, h = image.size
                        scale = min(1, 1000 / max(w, h))
                        page = merged.new_page(width=w*scale, height=h*scale)
                        page.insert_image(page.rect, stream=buf.getvalue())
                page_names.append(filename)
                if len(merged) > MAX_PAGES:
                    raise ValueError("Upload up to 30 pages or photos at a time.")
        if not len(merged):
            raise ValueError("The document contains no pages.")
        return merged.tobytes(garbage=3, deflate=True), page_names