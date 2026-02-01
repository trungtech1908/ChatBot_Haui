from langchain_core.output_parsers import StrOutputParser
from .config import AgentState, llm_gemini
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate


# --- System: KHÔNG có biến ---
system_prompt = SystemMessagePromptTemplate.from_template(
    """Bạn là chuyên gia tối ưu hóa truy vấn cho hệ thống RAG (Retrieval-Augmented Generation).
Nhiệm vụ của bạn là chuyển đổi truy vấn gốc của người dùng **(là một sinh viên Trường Đại Học Công Nghiệp Hà Nội)** thành một câu hỏi hoặc cụm từ tìm kiếm rõ ràng, ngắn gọn, đầy đủ ngữ cảnh, dễ hiểu và tối ưu để tra cứu trong cơ sở tri thức vector.

**Quy tắc bắt buộc:**
1. Giữ nguyên ý định cốt lõi của người dùng.
2. Loại bỏ từ thừa, lặp lại, ngôn ngữ đời thường không cần thiết.
4. Chuyển thành dạng câu hỏi hoàn chỉnh hoặc cụm từ tìm kiếm mạnh (keyword-rich).
5. Nếu truy vấn bằng tiếng Việt, trả về query tối ưu bằng tiếng Việt.
6. **Chuyển đổi từ lóng, từ đời thường sang từ ngữ chính thức với nghĩa ngắn gọn, chi tiết:**  
   - "phao" → "nhìn trộm tài liệu"  
   - "quay cóp" → "nhìn bài người khác"  
   - Các từ lóng khác cũng phải được chuyển thành ngôn ngữ chuẩn, dễ tìm kiếm.
7. Không thêm thông tin ngoài truy vấn gốc.
8. Chỉ trả về đúng **1 query tối ưu**, không giải thích, không dấu đầu dòng.

Input truy vấn gốc sẽ được cung cấp ở tin nhắn người dùng.  
"""
)




human_prompt = HumanMessagePromptTemplate.from_template("{user_query}")

prompt = ChatPromptTemplate.from_messages([
    system_prompt,
    human_prompt
])

def node_query_transform(state: AgentState) -> AgentState:
    chain = prompt | llm_gemini | StrOutputParser()
    state['new_query'] = chain.invoke({'user_query': state['query']})
    return state

# input_state = AgentState(query='ererfffe')
# res = node_query_transform(input_state)
# print(res['new_query'])
