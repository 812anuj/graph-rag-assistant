
import streamlit as st

from src.config.settings import Settings
from src.graph.neo4j_connection import Neo4jConnection
from src.retrieval.graph_rag_retriever import GraphRAGRetriever


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Graph RAG Assistant",
    page_icon="🧠",
    layout="wide"
)

st.title("🧠 Graph RAG Assistant")

st.markdown(
    "Ask questions about the Interactive Platform for Blood Donation."
)


# --------------------------------------------------
# INITIALIZE BACKEND
# --------------------------------------------------

@st.cache_resource
def initialize_backend():

    settings = Settings()

    connection = Neo4jConnection(settings)

    connection.verify_connection()

    retriever = GraphRAGRetriever(
        connection,
        settings
    )

    return connection, retriever


try:

    connection, retriever = initialize_backend()

    st.success("Connected to Neo4j successfully!")

except Exception as e:

    st.error(f"Backend connection failed: {e}")

    st.stop()


# --------------------------------------------------
# CHAT HISTORY
# --------------------------------------------------

if "messages" not in st.session_state:

    st.session_state.messages = []


for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# --------------------------------------------------
# USER INPUT
# --------------------------------------------------

question = st.chat_input("Ask your question here...")


if question:

    st.session_state.messages.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):

        st.markdown(question)


    with st.chat_message("assistant"):

        with st.spinner(
            "Searching knowledge graph and generating answer..."
        ):

            try:

                # Run Graph RAG pipeline
                results = retriever.retrieve(
                    question=question,
                    top_k=5,
                    max_hops=2
                )

                # Display detected entity
                st.caption(
                    f"Detected entity: {results['entity_name']}"
                )

                answer = results["answer"]

                sources = results["sources"]

                # Display generated answer
                st.markdown(answer)


                # ------------------------------------------
                # SOURCE PASSAGES
                # ------------------------------------------

                with st.expander("📚 View Retrieved Source Passages"):

                    if sources:

                        for source in sources:

                            st.markdown(
                                f"**Chunk ID:** `{source['chunk_id']}`"
                            )

                            st.markdown(
                                f"**PDF Page:** {source['page_number']}"
                            )

                            st.write("**Similarity Score:**", source["score"])
                            st.write("**Retrieved Through:**", source["retrieval_sources"])
                            
                            st.markdown("**Passage:**")

                            st.write(source["text"])
                            
                            st.divider()

                    else:

                        st.info(
                            "No source passages available."
                        )


                # Save assistant answer in chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": answer
                })


            except Exception as e:

                st.error(f"Something went wrong: {e}")
