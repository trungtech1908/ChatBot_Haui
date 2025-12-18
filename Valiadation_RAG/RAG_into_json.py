from graph import res
import os
import json

dir_path = "Validation"
output_dir = f"{dir_path}_RAG"

# tạo thư mục mới nếu chưa tồn tại
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(dir_path):
    if not filename.endswith(".json"):
        continue

    input_path = os.path.join(dir_path, filename)

    with open(input_path, "r", encoding="utf-8") as f:
        contents = json.load(f)

    rag_results = []

    for content in contents:
        question = content["Question"]

        result = res(question)
        answer = result["answer"]
        category = result["category"]

        rag_results.append({
            "Question": question,
            "Category": category,
            "Answer": answer
        })

    output_filename = filename.replace(".json", "_RAG.json")
    output_path = os.path.join(output_dir, output_filename)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(rag_results, f, ensure_ascii=False, indent=2)