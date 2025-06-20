import streamlit as st
import os
import json
import uuid
import time
from confluent_kafka import Producer, Consumer

# === Load Kafka secrets ===
BOOTSTRAP_SERVERS = st.secrets["KAFKA_BOOTSTRAP"]
API_KEY = st.secrets["KAFKA_API_KEY"]
API_SECRET = st.secrets["KAFKA_API_SECRET"]

# === Kafka Configuration ===
conf_producer = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'security.protocol': 'SASL_SSL',
    'sasl.mechanisms': 'PLAIN',
    'sasl.username': API_KEY,
    'sasl.password': API_SECRET
}
producer = Producer(conf_producer)

conf_consumer = conf_producer.copy()
conf_consumer.update({
    'group.id': 'streamlit-ui',
    'auto.offset.reset': 'earliest'
})
consumer = Consumer(conf_consumer)
consumer.subscribe(['llm_answers'])

# === Streamlit UI Configuration ===
st.set_page_config(page_title="🧠 IT Asset Policy Assistant", page_icon="💼", layout="centered")

st.markdown("""
    <style>
        body {
            background-color: #f9fafb;
        }
        .main-title {
            text-align: center;
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 0.2em;
        }
        .subtitle {
            text-align: center;
            font-size: 1.1em;
            color: #555;
            margin-bottom: 2em;
        }
        .chat-box {
            background-color: #ffffff;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        .answer {
            background-color: #e7f6e7;
            border-left: 5px solid #2ecc71;
            padding: 1rem;
            margin-top: 1.5rem;
            border-radius: 6px;
            font-size: 1.05rem;
        }
        .submit-btn {
            background-color: #4CAF50;
            color: white;
            padding: 10px 24px;
            border: none;
            border-radius: 6px;
            font-size: 1rem;
            transition: 0.3s;
        }
        .submit-btn:hover {
            background-color: #45a049;
        }
    </style>
""", unsafe_allow_html=True)

# === Header ===
st.markdown("<div class='main-title'>💬 Ask Your IT Asset Policy Assistant</div>", unsafe_allow_html=True)
st.markdown("<div class='subtitle'>Get instant answers to IT policy questions via Kafka-powered assistant</div>", unsafe_allow_html=True)

# === Input Section ===
with st.container():
    st.markdown("<div class='chat-box'>", unsafe_allow_html=True)

    user_question = st.text_input("🔍 Type your question below:", placeholder="E.g. What happens if I lose my laptop?", key="user_input")

    if st.button("🚀 Submit", key="submit", help="Click to submit your question"):
        if not user_question.strip():
            st.warning("⚠️ Please enter a valid question.")
        else:
            event_id = str(uuid.uuid4())
            message = {"event_id": event_id, "question": user_question}

            try:
                producer.produce("user_questions", key=event_id, value=json.dumps(message))
                producer.flush()
                st.success("✅ Question submitted. Awaiting response...")
            except Exception as e:
                st.error(f"❌ Failed to send to Kafka: {e}")
                st.stop()

            with st.spinner("🤖 Waiting for response from assistant..."):
                start_time = time.time()
                timeout = 30

                while True:
                    msg = consumer.poll(timeout=3.0)
                    if msg is None:
                        if time.time() - start_time > timeout:
                            st.error("⌛ Timed out waiting for answer.")
                            break
                        continue

                    try:
                        response_data = json.loads(msg.value().decode("utf-8"))
                        if response_data.get("event_id") == event_id:
                            answer = response_data.get("answer", "No answer returned.")
                            st.markdown(f"<div class='answer'>{answer}</div>", unsafe_allow_html=True)
                            break
                    except Exception as e:
                        st.error(f"⚠️ Error decoding message: {e}")
                        break

    st.markdown("</div>", unsafe_allow_html=True)

# === Footer ===
st.markdown("---")
st.markdown("🔒 Secure, Kafka-powered Assistant · 💼 Developed by TCS FluxMakers", unsafe_allow_html=True)
