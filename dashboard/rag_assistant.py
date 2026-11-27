
import streamlit as st
import requests
import chromadb
import time

from google import genai
from google.genai import types


# Gemini model configuration
EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-3.8-flash"

MAX_RETRIES = 3


# Retry API calls when temporary errors occur
def call_with_retry(api_function, api_name):

    for attempt in range(MAX_RETRIES + 1):

        try:
            return api_function()

        except Exception as error:

            error_message = str(error).upper()

            temporary_error = (
                "503" in error_message
                or "UNAVAILABLE" in error_message
            )

            if temporary_error and attempt < MAX_RETRIES:

                wait_time = 2 ** (attempt + 1)

                print(
                    f"{api_name} failed. "
                    f"Retrying in {wait_time} seconds..."
                )

                time.sleep(wait_time)

            else:

                raise RuntimeError(
                    f"{api_name} FAILED: {error}"
                ) from error


# Create an in-memory vector database
@st.cache_resource
def get_vector_database():

    client = chromadb.Client()

    collection = client.get_or_create_collection(
        name="industrial_iot_knowledge"
    )

    return client, collection


# Convert text into embeddings
def create_embeddings(gemini, texts, task_type):

    vectors = []

    for start in range(0, len(texts), 16):

        batch = texts[start:start + 16]

        response = call_with_retry(
            lambda: gemini.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type=task_type
                )
            ),
            "EMBEDDING API"
        )

        vectors.extend([
            item.values for item in response.embeddings
        ])

    return vectors


# Collect machine information from FastAPI
def collect_machine_documents(api_url):

    documents = []
    ids = []

    # Get latest machine readings
    response = requests.get(
        f"{api_url}/machines/live",
        timeout=15
    )

    response.raise_for_status()

    machines = response.json().get("machines", [])

    for machine in machines:

        machine_id = str(machine["machine_id"])

        documents.append(
            f"""
            Latest machine reading.
            Machine ID: {machine_id}
            Machine name: {machine.get('machine_name')}
            Temperature: {machine.get('temperature')} Celsius
            Power: {machine.get('power')}
            Current: {machine.get('current')}
            Production count: {machine.get('production_count')}
            Status: {machine.get('status')}
            Stop reason: {machine.get('stop_reason_code')}
            """
        )

        ids.append(f"live_{machine_id}")

        # Get historical readings
        history_response = requests.get(
            f"{api_url}/machines/{machine_id}/history",
            timeout=15
        )

        history_response.raise_for_status()

        history = history_response.json().get("history", [])

        for index, reading in enumerate(history[:10]):

            documents.append(
                f"""
                Historical machine reading.
                Machine ID: {machine_id}
                Timestamp: {reading.get('timestamp')}
                Temperature: {reading.get('temperature')}
                Production count: {reading.get('production_count')}
                Status: {reading.get('status')}
                Stop reason: {reading.get('stop_reason_code')}
                Anomaly: {reading.get('is_anomaly')}
                """
            )

            ids.append(f"history_{machine_id}_{index}")

    # Troubleshooting knowledge
    troubleshooting = [

        "E101 means Power Failure. Check the machine power supply and electrical connections.",

        "E102 means Motor Overheating. Check motor temperature, cooling and ventilation.",

        "E103 means Material Shortage. Check the raw material supply.",

        "E104 means Emergency Stop. Check the emergency stop button and safety conditions.",

        "Machine status 1 means Running.",

        "Machine status 0 means Stopped.",

        "Temperature below 0 or above 90 degrees Celsius is considered an anomaly in this project's configured rule."

    ]

    for index, document in enumerate(troubleshooting):

        documents.append(document)

        ids.append(f"troubleshooting_{index}")

    return ids, documents


# Build the RAG knowledge base
def build_knowledge_base(api_url, gemini, collection):

    ids, documents = collect_machine_documents(api_url)

    if not documents:

        raise ValueError(
            "No machine information found."
        )

    # Create embeddings
    embeddings = create_embeddings(
        gemini,
        documents,
        "RETRIEVAL_DOCUMENT"
    )

    # Remove old information only after new embeddings succeed
    old_ids = collection.get()["ids"]

    if old_ids:

        collection.delete(ids=old_ids)

    # Store new information in ChromaDB
    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings
    )

    return len(documents)


# Retrieve relevant information and generate an answer
def ask_rag_question(question, gemini, collection):

    total_records = collection.count()

    if total_records == 0:

        raise ValueError(
            "Knowledge base is empty. Refresh machine knowledge."
        )

    # Convert question into embedding
    question_embedding = create_embeddings(
        gemini,
        [question],
        "RETRIEVAL_QUERY"
    )[0]

    # Retrieve relevant documents
    results = collection.query(
        query_embeddings=[question_embedding],
        n_results=min(5, total_records)
    )

    retrieved_documents = results["documents"][0]

    if not retrieved_documents:

        raise ValueError(
            "No relevant information found."
        )

    context = "\n\n".join(retrieved_documents)

    # Prepare prompt
    prompt = f"""
    You are an Industrial IoT Machine Analytics Assistant.

    Answer the user's question using only the retrieved information.

    If the answer is not available in the retrieved information,
    clearly say that the available data is insufficient.

    Do not invent machine readings or stop reasons.

    Retrieved information:
    {context}

    User question:
    {question}
    """

    # Generate answer using Gemini
    response = call_with_retry(
        lambda: gemini.models.generate_content(
            model=GENERATION_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2
            )
        ),
        "TEXT GENERATION API"
    )

    if not response.text:

        raise ValueError(
            "Gemini returned an empty response."
        )

    return response.text, retrieved_documents


# Display the chatbot in Streamlit
def render_rag_assistant(api_url):

    st.title("AI Assistant")

    st.caption(
        "Ask questions about machine readings, history and troubleshooting."
    )

    # Gemini API key input
    api_key = st.text_input(
        "Gemini API Key",
        type="password",
        help="Enter your Google Gemini API key."
    )

    if not api_key:

        st.info(
            "Enter your Gemini API key to start the AI Assistant."
        )

        return

    # Connect to Gemini
    gemini = genai.Client(
        api_key=api_key
    )

    # Connect to ChromaDB
    db_client, collection = get_vector_database()

    # Initialize chat history
    if "rag_messages" not in st.session_state:

        st.session_state.rag_messages = []

    if "rag_ready" not in st.session_state:

        st.session_state.rag_ready = False

    # Refresh machine knowledge
    if st.button("Refresh Machine Knowledge"):

        st.session_state.rag_ready = False

        st.session_state.rag_messages = []

        st.rerun()

    # Display previous messages
    for message in st.session_state.rag_messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])

    # Chat input
    question = st.chat_input(
        "Ask about your industrial machines..."
    )

    if question:

        st.session_state.rag_messages.append({
            "role": "user",
            "content": question
        })

        try:

            with st.spinner(
                "Retrieving machine information..."
            ):

                # Build knowledge base first time
                if not st.session_state.rag_ready:

                    with st.status(
                        "Building machine knowledge base...",
                        expanded=True
                    ) as status:

                        count = build_knowledge_base(
                            api_url,
                            gemini,
                            collection
                        )

                        st.session_state.rag_ready = True

                        status.update(
                            label=f"Knowledge base ready: {count} records",
                            state="complete"
                        )

                # Ask RAG question
                answer, sources = ask_rag_question(
                    question,
                    gemini,
                    collection
                )

            st.session_state.rag_messages.append({
                "role": "assistant",
                "content": answer
            })

        except Exception as error:

            st.session_state.rag_messages.append({
                "role": "assistant",
                "content": f"Error: {error}"
            })

        st.rerun()
