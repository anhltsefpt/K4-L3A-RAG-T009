import streamlit as st
from dotenv import load_dotenv

from src.task10_generation import generate_with_citation


load_dotenv()

st.set_page_config(
    page_title="RAG Chatbot",
    page_icon="",
    layout="wide",
)

if "messages" not in st.session_state:
    st.session_state.messages = []


def render_sources(sources: list[dict], retrieval_source: str) -> None:
    """Hiển thị nguồn map trực tiếp về SearchResult (không phải URL model bịa)."""
    if not sources:
        st.info("Không có nguồn nào được sử dụng (safe refusal).")
        return

    with st.expander(f"Nguồn ({len(sources)}) · retrieval: {retrieval_source}", expanded=True):
        for index, item in enumerate(sources, 1):
            metadata = item["metadata"]
            header = (
                f"**[{index}] {metadata.get('title', metadata['source'])}** "
                f"· `{item['retrieval_method']}` · score={item['score']:.4f}"
            )
            st.markdown(header)
            caption = f"{metadata['source']} · {metadata.get('doc_type', '')}"
            url = metadata.get("url")
            if url:
                caption += f" · [nguồn gốc]({url})"
            st.caption(caption)
            snippet = item["content"].strip().replace("\n", " ")
            st.markdown(f"> {snippet[:300]}{'…' if len(snippet) > 300 else ''}")


with st.sidebar:
    st.title("RAG Chatbot")
    st.caption("Corpus: học phí – học bổng – hỗ trợ tài chính sinh viên")
    top_k = st.slider("Số chunks", 3, 10, 5)

st.title("RAG Chatbot")
st.caption("Hỏi về học phí, học bổng và hỗ trợ tài chính — câu trả lời kèm trích dẫn kiểm chứng được.")

# Render lại lịch sử (giữ đủ sources để hiển thị nguồn của câu trả lời cũ)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(message.get("sources", []), message.get("retrieval_source", "none"))

query = st.chat_input("Nhập câu hỏi...")

if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    with st.chat_message("assistant"):
        with st.spinner("Đang truy xuất và tạo câu trả lời..."):
            result = generate_with_citation(query, top_k)
        st.markdown(result["answer"])
        render_sources(result["sources"], result["retrieval_source"])

    # Lưu đủ dữ liệu để render lại nguồn của câu trả lời này về sau
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
            "retrieval_source": result["retrieval_source"],
        }
    )
