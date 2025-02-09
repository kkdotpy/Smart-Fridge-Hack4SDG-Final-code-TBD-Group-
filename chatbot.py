import pickle
import pandas as pd
from datetime import datetime
from groq import Groq
import streamlit as st
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Access the API keys
api_key = os.getenv('API_KEY')


def chatbot_page():
    def get_inventory():
        # Load the inventory from the database.pkl file
        df = pd.DataFrame()
        with open('database.pkl', 'rb') as f:
            df = pickle.load(f)
        
        # Format the inventory content as a string
        items = ''
        for index, row in df.iterrows():
            items += str(row) + '\n'  # Adding newline for better readability
        
        return items

    def response(question):
        # Get the current inventory from the fridge
        inventory = get_inventory()

        # Initialize the Groq client with API key
        client = Groq(api_key=api_key)

        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {
                    "role": "user",
                    "content": "you are a smart chatbot and will answer anything about inventory related question that i have in this fridge below is the content of my fridge "+inventory+" and this is today's date "+str(datetime.now())
                },
                {
                    "role": "assistant",
                    "content": "I'm glad to help with your inventory-related questions!, Please go ahead and ask your question, and I'll do my best to help you with your inventory query!"
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stop=None,
    )    # Return the assistant's response
        return completion.choices[0].message.content

    st.title('Chill Buddy')
    with st.form(key='Details'):
        q = st.text_input('Ask any questions?')

        submit_button = st.form_submit_button(label='Submit')
        if submit_button:
            st.write(response(q))
        
    st.button('Ask another question!')