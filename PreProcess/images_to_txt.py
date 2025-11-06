import os
from google import genai
from PIL import Image
from dotenv import load_dotenv
load_dotenv()
# --- Gemini API ---
client = genai.Client()

image_root = "images"
output_root = "output_md"
os.makedirs(output_root, exist_ok=True)

def extract_text_from_image(img_path: str) -> str:
    pil_img = Image.open(img_path)

    prompt = (
        "Extract all text from the image, including tables, "
        "and return in **Markdown format** to preserve **bold**, *italic*, "
        "tables, and lists for RAG embedding."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",  # GIỮ NGUYÊN MODEL CỦA BẠN
        contents=[prompt, pil_img]
    )
    return response.text.strip()


# --- Duyệt thư mục ---
for folder1 in os.listdir(image_root):
    folder1_path = os.path.join(image_root, folder1)
    if not os.path.isdir(folder1_path):
        continue

    for pdf_folder in os.listdir(folder1_path):
        pdf_folder_path = os.path.join(folder1_path, pdf_folder)
        if not os.path.isdir(pdf_folder_path):
            continue

        # Sắp xếp ảnh theo số trong tên file
        images_list = sorted(
            [f for f in os.listdir(pdf_folder_path)
             if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".tiff"))],
            key=lambda x: int(''.join(filter(str.isdigit, x)) or 0)
        )

        md_lines = []

        for img_file in images_list:
            img_path = os.path.join(pdf_folder_path, img_file)
            try:
                text_md = extract_text_from_image(img_path)
                if text_md:
                    md_lines.append(text_md)
            except Exception as e:
                print(f"[Lỗi OCR] {img_path}: {e}")
                md_lines.append("")  # Trang lỗi → để trống

        # --- LƯU FILE .md: CHỈ 1 DÒNG TRỐNG GIỮA CÁC TRANG ---
        md_path = os.path.join(output_root, f"{pdf_folder}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(md_lines))  # CHỈ 1 DÒNG TRỐNG

        print(f"Đã lưu: {md_path}")

print("Hoàn tất OCR → Markdown (1 dòng trống giữa các trang).")