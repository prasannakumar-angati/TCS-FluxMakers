import streamlit as st
from confluent_kafka import Producer, Consumer
import json
import uuid
import time

# =======================
# Kafka Configuration
# =======================
BOOTSTRAP_SERVERS = 'pkc-l7pr2.ap-south-1.aws.confluent.cloud:9092'
KAFKA_API_KEY = 'ALF2Y6LYWTBA32J6'
KAFKA_API_SECRET = '/2hB2DViCaK6YaIu/tvOrKiSpfbeUMnkhAAGA3+xl4FwBz9AUyWrt6iiUA8RYnHE'

# Kafka Topics
QUESTION_TOPIC = "user_questions"
RESPONSE_TOPIC = "llm_answers"

# =======================
# Kafka Producer
# =======================
producer_conf = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': KAFKA_API_KEY,
    'sasl.password': KAFKA_API_SECRET
}
producer = Producer(producer_conf)

# =======================
# Kafka Consumer
# =======================
consumer_conf = {
    'bootstrap.servers': BOOTSTRAP_SERVERS,
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': KAFKA_API_KEY,
    'sasl.password': KAFKA_API_SECRET,
    'group.id': 'streamlit-ui-group',
    'auto.offset.reset': 'latest'
}
consumer = Consumer(consumer_conf)
consumer.subscribe([RESPONSE_TOPIC])

# =======================
# Streamlit UI
# =======================
st.set_page_config(page_title="🧠 IT Policy Assistant", layout="centered")
st.title("🧠 Ask Your IT Asset Policy Assistant")

question = st.text_input("💬 Enter your question:")

if st.button("Submit"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        question_id = str(uuid.uuid4())
        st.info("Sending your question to the assistant...")

        # Send question to Kafka
        message = {
            "id": question_id,
            "text": question
        }
        producer.produce(QUESTION_TOPIC, key=question_id, value=json.dumps(message))
        producer.flush()
        st.write("⏳ Waiting for answer from LLM...")

        # Wait for answer from llm_answers topic
        answer = None
        timeout = 15  # seconds
        start_time = time.time()

        while time.time() - start_time < timeout:
            msg = consumer.poll(1.0)
            if msg is None:
                continue
            if msg.error():
                st.error(f"Kafka error: {msg.error()}")
                break

            response = json.loads(msg.value().decode('utf-8'))
            if response.get("id") == question_id:
                answer = response.get("answer")
                break

        if answer:
            st.success(f"✅ Answer: {answer}")
        else:
            st.error("⚠️ No response received in time. Please try again.")
