import streamlit as st
from data_handler import (
    VectorDB,
    scrape_reddit,
    hybrid_search,
    rerank_llm,
    synthesize_answer
)
from utils import chunk_text

def main():
    st.set_page_config(page_title="Reddit RAG Chatbot", page_icon="🤖", layout="wide")
    st.title("🔍 Reddit RAG Chatbot")
    st.markdown("Ask questions about any topic and get answers based on real Reddit discussions!")

    # Initialize session state
    if "db" not in st.session_state:
        st.session_state.db = None
    if "topic" not in st.session_state:
        st.session_state.topic = ""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False

    # Sidebar: topic & load controls
    with st.sidebar:
        st.header("Settings")
        topic = st.text_input("Enter a topic to search on Reddit:", placeholder="e.g., movies")
        if st.button("Load Reddit Data"):
            if not topic:
                st.warning("Please enter a topic first.")
            else:
                st.session_state.topic = topic
                st.session_state.messages = []
                st.session_state.data_loaded = False
                try:
                    with st.spinner("Scraping Reddit..."):
                        text = scrape_reddit(topic)
                    if not text:
                        st.error("No data found on Reddit for this topic.")
                    else:
                        with st.spinner("Processing and indexing..."):
                            chunks = chunk_text(text)
                            if not chunks:
                                st.error("No valid text chunks could be created.")
                            else:
                                db_name = f"reddit_{topic.replace(' ', '_').lower()}"
                                st.session_state.db = VectorDB(db_name)
                                st.session_state.db.clear()
                                st.session_state.db.add(chunks)
                                st.session_state.data_loaded = True
                                st.success(f"Loaded {len(chunks)} chunks from Reddit data!")
                except Exception as e:
                    st.error(f"Error loading data: {e}")

        if st.session_state.data_loaded:
            st.success(f"✅ Data loaded for: {st.session_state.topic}")
            if st.button("Clear Chat History"):
                st.session_state.messages = []
            if st.button("Clear Indexed Data"):
                st.session_state.db = None
                st.session_state.data_loaded = False
                st.success("Cleared indexed data.")

        st.markdown("---")
        st.markdown("Tip: Type `/raw` as a question to see raw and reranked candidates for debugging.")

    # Main chat area
    col1, col2 = st.columns([3, 1])
    with col1:
        st.header("Chat")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        user_input = st.chat_input("Ask a question about the topic...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            # Generate response
            with st.chat_message("assistant"):
                if not st.session_state.data_loaded or not st.session_state.db:
                    warning_msg = "Please load Reddit data first using the sidebar!"
                    st.warning(warning_msg)
                    st.session_state.messages.append({"role": "assistant", "content": warning_msg})
                else:
                    try:
                        with st.spinner("Searching Reddit data..."):
                            candidates = hybrid_search(st.session_state.db, user_input)
                            reranked = rerank_llm(user_input, candidates)

                        if user_input.strip().lower() == "/raw":
                            st.markdown("**Raw candidates:**")
                            st.write(candidates)
                            st.markdown("**Reranked candidates:**")
                            st.write(reranked)
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": "Displayed raw and reranked candidates."
                            })
                        else:
                            answer = synthesize_answer(user_input, reranked)
                            st.markdown(answer)
                            st.session_state.messages.append({"role": "assistant", "content": answer})
                    except Exception as e:
                        err = f"Error generating response: {e}"
                        st.error(err)
                        st.session_state.messages.append({"role": "assistant", "content": err})

    with col2:
        st.header("Info")
        st.markdown(f"Topic: **{st.session_state.topic or 'None'}**")
        st.markdown("Commands:")
        st.markdown("- `/raw` : show raw & reranked candidates")
        st.markdown("- Use sidebar to load/clear data")

if __name__ == "__main__":
    main()