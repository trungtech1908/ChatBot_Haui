import os
from google import genai
from PIL import Image

# --- Gemini API ---
client = genai.Client()

image_root = "images"
output_root = "output_txt"
os.makedirs(output_root, exist_ok=True)

def extract_text_from_image(img_path):
    pil_img = Image.open(img_path)

    prompt_text = "Extract all text including tables as plain text suitable for RAG embedding."

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt_text, pil_img]
    )
    return response.text

# --- Duyệt folder ---
for folder1 in os.listdir(image_root):
    folder1_path = os.path.join(image_root, folder1)
    if not os.path.isdir(folder1_path):
        continue

    for pdf_folder in os.listdir(folder1_path):
        pdf_folder_path = os.path.join(folder1_path, pdf_folder)
        if not os.path.isdir(pdf_folder_path):
            continue

        pdf_txt_lines = []
        images_list = sorted([f for f in os.listdir(pdf_folder_path)
                              if f.lower().endswith((".png", ".jpg", ".jpeg"))])

        for img_file in images_list:
            img_path = os.path.join(pdf_folder_path, img_file)
            text = extract_text_from_image(img_path)
            pdf_txt_lines.append(text.strip())

        # --- Lưu TXT RAG-ready ---
        txt_path = os.path.join(output_root, f"{pdf_folder}.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write("\n\n".join(pdf_txt_lines))

        print(f"Saved TXT for RAG: {txt_path}")

print("Hoàn tất trích xuất text + bảng từ tất cả PDF.")
