import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="🤖",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.title("RAG Chatbot")
    st.caption("Hỏi đáp về chính sách học bổng, học phí, hỗ trợ tài chính")
    top_k = st.slider("Số chunks", 3, 10, 5)

st.title("RAG Chatbot")
st.caption("Hỏi về học bổng, học phí, hỗ trợ tài chính sinh viên")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "sources" in message and message["sources"]:
            with st.expander("📚 Nguồn tham khảo"):
                for i, src in enumerate(message["sources"], 1):
                    meta = src["metadata"]
                    st.markdown(
                        f"**[{i}] {meta.get('title', 'Unknown')}**  \n"
                        f"Nguồn: {meta.get('source', 'Unknown')}  \n"
                        f"Loại: {meta.get('doc_type', 'Unknown')}  \n"
                        f"Score: {src.get('score', 0):.3f}  \n"
                        f"Method: {src.get('retrieval_method', 'Unknown')}"
                    )

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})

    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang tìm kiếm và tạo câu trả lời..."):
            try:
                result = generate_with_citation(query, top_k=top_k)
                answer = result["answer"]
                sources = result["sources"]
                retrieval_source = result.get("retrieval_source", "unknown")
            except Exception as e:
                answer = f"❌ Lỗi: {str(e)}"
                sources = []
                retrieval_source = "error"

        st.markdown(answer)

        if sources:
            with st.expander("📚 Nguồn tham khảo"):
                for i, src in enumerate(sources, 1):
                    meta = src["metadata"]
                    st.markdown(
                        f"**[{i}] {meta.get('title', 'Unknown')}**  \n"
                        f"Nguồn: {meta.get('source', 'Unknown')}  \n"
                        f"Loại: {meta.get('doc_type', 'Unknown')}  \n"
                        f"Score: {src.get('score', 0):.3f}  \n"
                        f"Method: {src.get('retrieval_method', 'Unknown')}"
                    )

    st.session_state.messages.append({
        "role": "assistant", 
        "content": answer,
        "sources": sources,
        "retrieval_source": retrieval_source
    })