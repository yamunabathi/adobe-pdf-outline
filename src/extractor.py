import fitz  # PyMuPDF
import os
import json
import statistics
import re

BOLD_FLAG = 2  # PyMuPDF span flag for bold

def looks_bold(span):
    return (span["flags"] & BOLD_FLAG) != 0 or "bold" in span["font"].lower()

def is_heading(span, page_median_size):
    text = span["text"].strip()
    if not text or len(text) < 3:
        return None
    size = span["size"]
    bold = looks_bold(span)
    numbered = bool(re.match(r"^(\d+(\.\d+)*)\s+.+", text))
    if size >= page_median_size + 6 and (bold or numbered):
        return "H1"
    if size >= page_median_size + 3:
        return "H2"
    if size >= page_median_size + 1:
        return "H3"
    return None

def clean_incomplete_title(title):
    # Remove trailing prepositions/articles etc.
    words = title.strip().split()
    if words and words[-1].lower() in ["of", "in", "the", "a", "an", "and"]:
        words = words[:-1]
    return " ".join(words)

def guess_title(doc):
    first_page = doc[0]
    blocks = first_page.get_text("dict")["blocks"]
    title_candidates = []

    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                text = span["text"].strip()
                if len(text) < 3:
                    continue
                size = span["size"]
                if size < 12:
                    continue
                if looks_bold(span):
                    y0 = span.get("bbox", [0, 0, 0, 0])[1]
                    title_candidates.append((size, -y0, text, span["font"]))

    if title_candidates:
        title_candidates.sort(reverse=True)
        top_size = title_candidates[0][0]
        top_candidates = [c for c in title_candidates if abs(c[0] - top_size) < 0.5]
        if top_candidates:
            merged_title = " ".join(c[2] for c in sorted(top_candidates, key=lambda x: x[1]))
            merged_title = clean_incomplete_title(merged_title)
            if len(merged_title.split()) > 10:
                merged_title = " ".join(merged_title.split()[:10]) + "..."
            return merged_title.strip()

    fallback_lines = []
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            line_text = " ".join(span["text"].strip() for span in line["spans"])
            line_text = re.sub(r'\s+', ' ', line_text).strip()
            if line_text.lower() in ["page 1", "index", "contents", ""]:
                continue
            if len(line_text.split()) >= 2:
                fallback_lines.append(line_text)
            if len(fallback_lines) >= 2:
                break
        if len(fallback_lines) >= 2:
            break

    if fallback_lines:
        guess = fallback_lines[0]
        guess = clean_incomplete_title(guess)
        if len(guess.split()) > 5:
            guess = " ".join(guess.split()[:5]) + "..."
        return f"{guess} (inferred - untitled PDF)"

    return "Untitled Summary (inferred - untitled PDF)"

def extract_outline_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    outline = []

    page_medians = []
    for page in doc:
        sizes = [span["size"] for block in page.get_text("dict")["blocks"]
                 if "lines" in block for line in block["lines"]
                 for span in line["spans"]]
        page_medians.append(statistics.median(sizes) if sizes else 0)

    last_added = None

    for page_idx, page in enumerate(doc, start=1):
        page_median = page_medians[page_idx - 1]
        blocks = page.get_text("dict")["blocks"]

        buffer_text = ""
        buffer_level = None
        buffer_size = None

        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text:
                        continue
                    level = is_heading(span, page_median)
                    if level:
                        if buffer_level and (level == buffer_level or span["size"] == buffer_size):
                            buffer_text += " " + text
                        else:
                            if buffer_text:
                                item = {"level": buffer_level, "text": buffer_text.strip(), "page": page_idx}
                                if item != last_added:
                                    outline.append(item)
                                    last_added = item
                            buffer_text = text
                            buffer_level = level
                            buffer_size = span["size"]
                    else:
                        if buffer_text:
                            item = {"level": buffer_level, "text": buffer_text.strip(), "page": page_idx}
                            if item != last_added:
                                outline.append(item)
                                last_added = item
                            buffer_text = ""
                            buffer_level = None
                            buffer_size = None

        if buffer_text:
            item = {"level": buffer_level, "text": buffer_text.strip(), "page": page_idx}
            if item != last_added:
                outline.append(item)
                last_added = item

    title = guess_title(doc)
    return {
        "title": title,
        "outline": outline
    }

def process_pdfs(input_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    pdfs = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]

    if not pdfs:
        print("⚠️ No PDFs found in:", input_dir)
        return

    print(f"🟢 Found {len(pdfs)} PDF(s). Processing...")
    for filename in pdfs:
        pdf_path = os.path.join(input_dir, filename)
        print(f"➡️  Processing {filename} ...")
        try:
            result = extract_outline_from_pdf(pdf_path)
            output_path = os.path.join(output_dir, filename[:-4] + ".json")
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=4, ensure_ascii=False)
            print(f"✅ Wrote: {output_path}")
        except Exception as e:
            print(f"❌ Failed on {filename}: {e}")

if __name__ == "__main__":
    INPUT_DIR = "/app/input"
    OUTPUT_DIR = "/app/output"
    print("🚀 Starting outline extraction ...")
    print(f"📥 Input dir:  {INPUT_DIR}")
    print(f"📤 Output dir: {OUTPUT_DIR}")
    process_pdfs(INPUT_DIR, OUTPUT_DIR)
    print("🏁 Done.") 
# import fitz  # PyMuPDF
# import os
# import json
# import statistics
# import re

# BOLD_FLAG = 2  # PyMuPDF span flag for bold


# def looks_bold(span):
#     return (span["flags"] & BOLD_FLAG) != 0 or "bold" in span["font"].lower()


# def is_heading(span, page_median_size):
#     text = span["text"].strip()
#     if not text or len(text) < 3:
#         return None
#     size = span["size"]
#     bold = looks_bold(span)
#     numbered = bool(re.match(r"^(\d+(\.\d+)*)\s+.+", text))
#     if size >= page_median_size + 6 and (bold or numbered):
#         return "H1"
#     if size >= page_median_size + 3:
#         return "H2"
#     if size >= page_median_size + 1:
#         return "H3"
#     return None


# def clean_incomplete_title(title):
#     words = title.strip().split()
#     if words and words[-1].lower() in ["of", "in", "the", "a", "an", "and"]:
#         words = words[:-1]
#     return " ".join(words)

# import re

# import re

# def normalize_line(spans):
#     """Merge split-character spans into proper words."""
#     spans = sorted(spans, key=lambda x: x[0])  # sort by x0
#     line = ""
#     last_x = None
#     for x0, text in spans:
#         if last_x is not None and x0 - last_x > 5:  # small gap threshold
#             line += " "
#         line += text
#         last_x = x0 + len(text) * 2  # approximate width
#     return re.sub(r'\s+', ' ', line).strip()
# import re

# def normalize_line(spans):
#     """Merge spans into full line text using x0 order."""
#     spans = sorted(spans, key=lambda x: x[0])  # sort by x0
#     line = ""
#     last_x = None
#     for x0, text in spans:
#         if last_x is not None and x0 - last_x > 3:  # small gap → space
#             line += " "
#         line += text
#         last_x = x0 + len(text) * 2  # estimate width
#     return re.sub(r'\s+', ' ', line).strip()

# def is_title_case(text):
#     """Heuristic: Check if text looks like proper title casing."""
#     words = text.split()
#     if not words:
#         return False
#     return all(w[0].isupper() for w in words if w.isalpha())

# import re

# def normalize_line(spans):
#     """Merge split-character spans into proper words."""
#     spans = sorted(spans, key=lambda x: x[0])  # sort by x0
#     line = ""
#     last_x = None
#     for x0, text in spans:
#         if last_x is not None and x0 - last_x > 5:  # small gap threshold
#             line += " "
#         line += text
#         last_x = x0 + len(text) * 2  # approximate width
#     return re.sub(r'\s+', ' ', line).strip()
# def guess_title(doc):
#     first_page = doc[0]
#     blocks = first_page.get_text("dict")["blocks"]
#     line_map = {}

#     # Group spans by (font size, y-position) — treat them as same line
#     for block in blocks:
#         if "lines" not in block:
#             continue
#         for line in block["lines"]:
#             for span in line["spans"]:
#                 text = span["text"].strip()
#                 if not text or len(text) < 1:
#                     continue
#                 size = round(span["size"], 1)
#                 if size < 12:
#                     continue
#                 y0 = round(span.get("bbox", [0, 0, 0, 0])[1], 1)
#                 x0 = span.get("bbox", [0, 0, 0, 0])[0]
#                 key = (size, y0)
#                 if key not in line_map:
#                     line_map[key] = []
#                 line_map[key].append((x0, text))

#     if line_map:
#         # Sort by size descending and y ascending (top to bottom)
#         sorted_lines = sorted(line_map.items(), key=lambda x: (-x[0][0], x[0][1]))
#         top_size = sorted_lines[0][0][0]

#         top_lines = [item for item in sorted_lines if abs(item[0][0] - top_size) < 0.5]

#         merged_lines = []
#         for (_, _), spans in top_lines[:2]:  # take top 2 lines at most
#             line_text = normalize_line(spans)
#             merged_lines.append(line_text)

#         merged_title = " ".join(merged_lines)
#         merged_title = re.sub(r'\s+', ' ', merged_title).strip()
#         merged_title = clean_incomplete_title(merged_title)
#         merged_title = " ".join(merged_title.split()[:10])

#         # 🚨 Check for meaningless or incomplete titles
#         if len(merged_title.strip()) < 5 or len(merged_title.split()) < 2:
#             merged_title = None

#         if merged_title:
#             return merged_title + " (extracted title)"
#         # fall through to fallback if merged_title is garbage

#     # Fallback if no suitable title
#     fallback_lines = []
#     for block in blocks:
#         if "lines" not in block:
#             continue
#         for line in block["lines"]:
#             line_text = " ".join(span["text"].strip() for span in line["spans"])
#             line_text = re.sub(r'\s+', ' ', line_text).strip()
#             if line_text.lower() in ["page 1", "index", "contents", ""]:
#                 continue
#             if len(line_text.split()) >= 2:
#                 fallback_lines.append(line_text)
#             if len(fallback_lines) >= 2:
#                 break
#         if len(fallback_lines) >= 2:
#             break

#     if fallback_lines:
#         guess = fallback_lines[0]
#         guess = clean_incomplete_title(guess)
#         guess = " ".join(guess.split()[:10])
#         return f"{guess} (no title found - this is a suggested title for your PDF)"

#     return "Untitled Summary (no title found - this is a suggested title for your PDF)"










# def extract_outline_from_pdf(pdf_path):
#     doc = fitz.open(pdf_path)
#     outline = []
#     page_medians = []

#     for page in doc:
#         sizes = [span["size"] for block in page.get_text("dict")["blocks"]
#                  if "lines" in block for line in block["lines"]
#                  for span in line["spans"]]
#         page_medians.append(statistics.median(sizes) if sizes else 0)

#     last_added = None

#     for page_idx, page in enumerate(doc, start=1):
#         page_median = page_medians[page_idx - 1]
#         blocks = page.get_text("dict")["blocks"]

#         buffer_text = ""
#         buffer_level = None
#         buffer_size = None

#         for block in blocks:
#             if "lines" not in block:
#                 continue
#             for line in block["lines"]:
#                 for span in line["spans"]:
#                     text = span["text"].strip()
#                     if not text:
#                         continue
#                     level = is_heading(span, page_median)
#                     if level:
#                         if buffer_level and (level == buffer_level or span["size"] == buffer_size):
#                             buffer_text += " " + text
#                         else:
#                             if buffer_text:
#                                 item = {"level": buffer_level, "text": buffer_text.strip(), "page": page_idx}
#                                 if item != last_added:
#                                     outline.append(item)
#                                     last_added = item
#                             buffer_text = text
#                             buffer_level = level
#                             buffer_size = span["size"]
#                     else:
#                         if buffer_text:
#                             item = {"level": buffer_level, "text": buffer_text.strip(), "page": page_idx}
#                             if item != last_added:
#                                 outline.append(item)
#                                 last_added = item
#                             buffer_text = ""
#                             buffer_level = None
#                             buffer_size = None

#         if buffer_text:
#             item = {"level": buffer_level, "text": buffer_text.strip(), "page": page_idx}
#             if item != last_added:
#                 outline.append(item)
#                 last_added = item

#     title = guess_title(doc)
#     return {
#         "title": title,
#         "outline": outline
#     }


# def process_pdfs(input_dir, output_dir):
#     os.makedirs(output_dir, exist_ok=True)
#     pdfs = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]

#     if not pdfs:
#         print("⚠️ No PDFs found in:", input_dir)
#         return

#     print(f"🟢 Found {len(pdfs)} PDF(s). Processing...")
#     for filename in pdfs:
#         pdf_path = os.path.join(input_dir, filename)
#         print(f"➡️  Processing {filename} ...")
#         try:
#             result = extract_outline_from_pdf(pdf_path)
#             output_path = os.path.join(output_dir, filename[:-4] + ".json")
#             with open(output_path, "w", encoding="utf-8") as f:
#                 json.dump(result, f, indent=4, ensure_ascii=False)
#             print(f"✅ Wrote: {output_path}")
#         except Exception as e:
#             print(f"❌ Failed on {filename}: {e}")


# if __name__ == "__main__":
#     INPUT_DIR = "/app/input"
#     OUTPUT_DIR = "/app/output"
#     print("🚀 Starting outline extraction ...")
#     print(f"📥 Input dir:  {INPUT_DIR}")
#     print(f"📤 Output dir: {OUTPUT_DIR}")
#     process_pdfs(INPUT_DIR, OUTPUT_DIR)
#     print("🏁 Done.")
