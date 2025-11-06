import os
from pdf2image import convert_from_path

# 2 thư mục chứa PDF
folders = [
    "Fit_HaUI_Các quy định,quy chế mà SV cần biết",
    "QĐ về học phí áp dụng năm học 25-26"
]

# Thư mục gốc lưu ảnh
output_root = "images"

for folder in folders:
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.lower().endswith(".pdf"):
                pdf_path = os.path.join(root, file)

                # Tạo đường dẫn lưu ảnh dựa theo đường dẫn gốc + tên file
                relative_path = os.path.relpath(root, folder)
                pdf_name = os.path.splitext(file)[0]  # tên file không có .pdf
                output_folder = os.path.join(output_root, folder, relative_path, pdf_name)
                os.makedirs(output_folder, exist_ok=True)

                # Chuyển PDF sang ảnh
                pages = convert_from_path(pdf_path, dpi=200)
                for i, page in enumerate(pages, start=1):
                    image_path = os.path.join(output_folder, f"page_{i}.png")
                    page.save(image_path, "PNG")
                    print(f"Saved: {image_path}")

print("Hoàn tất tất cả PDF!")
