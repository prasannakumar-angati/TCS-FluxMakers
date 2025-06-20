# app.py

import streamlit as st
from dotenv import load_dotenv
import os
from confluent_kafka import Producer, Consumer
import json
import uuid

# Load secrets from .env file
load_dotenv("./app.env")

# Kafka config from environment variables
BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP")
API_KEY = os.getenv("KAFKA_API_KEY")
API_SECRET = os.getenv("KAFKA_API_SECRET")

# Kafka Producer config
conf_producer = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'security.protocol': 'SASL_SSL',
    'sasl.mechanisms': 'PLAIN',
    'sasl.username': API_KEY,
    'sasl.password': API_SECRET
}
producer = Producer(conf_producer)

# Kafka Consumer config
conf_consumer = conf_producer.copy()
conf_consumer.update({
    'group.id': 'streamlit-ui',
    'auto.offset.reset': 'earliest'
})
consumer = Consumer(conf_consumer)
consumer.subscribe(['llm_answers'])

# UI
st.set_page_config(page_title="GenAI IT Assistant", page_icon="🤖")
st.title("💬 Ask a Question About IT Asset Policy")

user_question = st.text_input("Ask your question here:")

if st.button("Submit"):
    if not user_question.strip():
        st.warning("Please enter a question.")
    else:
        event_id = str(uuid.uuid4())
        msg = {"event_id": event_id, "question": user_question}
        producer.produce("user_questions", key=event_id, value=json.dumps(msg))
        producer.flush()
        st.success("✅ Question sent to Kafka")

        st.info("⏳ Waiting for answer from backend...")

        # Poll for response
        while True:
            msg = consumer.poll(timeout=10.0)
            if msg is None:
                st.warning("Still waiting...")
                continue
            data = json.loads(msg.value().decode('utf-8'))
            if data.get("event_id") == event_id:
                st.subheader("💡 Answer:")
                st.write(data.get("answer", "No answer returned"))
                break
