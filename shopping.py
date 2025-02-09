import pickle
import pandas as pd
from datetime import datetime
from groq import Groq
import streamlit as st
import ast  # For converting string representation of a list into a Python list
import os
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()

# Access the API keys
api_key = os.getenv('API_KEY')

def shopping_page():
    # Load the dataset from the pickle file
    df = pd.DataFrame()
    with open('database.pkl', 'rb') as f:
        df = pickle.load(f)

    #--------------------------------------------------------------------------------------------------------------
    # Checking expiring or low-quantity items
    # 'For now we set items expiring in two days for alerts'
    def check_items(df):
        expiring_items = []
        low_quantity_items = []
        fridge_items = []
        alerts = []

        for index, rows in df.iterrows():
            # Check if the item is expiring within the next 2 days
            if (rows['Expiration'] - datetime.now()).days <= 2:
                expiring_items.append(rows['Item'])
                alerts.append(f"Expiring soon: {rows['Item']} (expires on {rows['Expiration']})")
                
            elif rows['Quantity'] <= 1:  # Assuming 1 as the low quantity threshold
                low_quantity_items.append(rows['Item'])
                alerts.append(f"Low quantity: {rows['Item']} (only {rows['Quantity']} left)")
                
            # Add all fridge items (expiring or not) to the fridge_items list for later checking
            fridge_items.append(rows['Item'])

        return expiring_items, low_quantity_items, fridge_items, alerts

    #-----------------------------------------------------------------------------------------------------------------
    # Generate a recipe based on items in the fridge
    def generate_recipe(expiring_items, fridge_items, preference):
        client = Groq(
            api_key=api_key
        )

        prompt = f"""
        Can you suggest a recipe using the following items that are expiring soon and should be prioritized? 
        These are expiring soon: {expiring_items}.
        These are the other items in my fridge: {fridge_items}.
        My preference is: {preference}.
        """
        
        # Call the Groq API to generate a recipe
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        recipe = completion.choices[0].message.content
        return recipe

    #-----------------------------------------------------------------------------------------------------------------
    # Ask Groq to return the missing items based on the recipe
    def get_missing_items(recipe, fridge_items):
        client = Groq(
            api_key=api_key
        )

        prompt = f"""
        Based on the following recipe:
        {recipe}
        
        These are the items I already have in my fridge: {fridge_items}.
        Please return only the ingredients that are missing from my fridge in the form of python list. strictly no other text besides the python list.
        """
        
        # Call the Groq API to return missing items
        completion = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_tokens=512,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        # Retrieve the response as a string, which is expected to be a Python list representation
        missing_items = completion.choices[0].message.content
        
        try:
            # Convert the string response into an actual Python list
            missing_items_list = ast.literal_eval(missing_items)
        except (ValueError, SyntaxError):
            missing_items_list = []
        
        return missing_items_list

    #--------------------------------------------------------------------------------------------------------
    # Filter out items that are already in the fridge from the missing items list
    def filter_missing_items(missing_items, fridge_items):
        filtered_missing_items = [item for item in missing_items if item not in fridge_items]
        return filtered_missing_items

    #--------------------------------------------------------------------------------------------------------
    # Combine the missing items with low-quantity items from the fridge
    def create_final_shopping_list(filtered_missing_items, low_quantity_items):
        # Combine missing items from the recipe with low-quantity items from the fridge
        shopping_list = filtered_missing_items + low_quantity_items
        return shopping_list

    #--------------------------------------------------------------------------------------------------------
    # Streamlit application setup
    st.title('Smart Fridge Recipe Recommender')

    with st.form(key='Details'):
        pref = st.text_input('Any special preferences?')

        submit_button = st.form_submit_button(label='Submit')
        if submit_button:
            # Step 1: Check for expiring, low quantity, and other items
            expiring_items, low_quantity_items, fridge_items, alerts = check_items(df)
            
            # Step 2: Generate a recipe using Groq
            recipe = generate_recipe(expiring_items, fridge_items, pref)
            
            st.write("### Recipe Suggested:")
            st.write(recipe)

            # Step 3: Ask Groq to return the missing items for the recipe
            missing_items_list = get_missing_items(recipe, fridge_items)
            
            # Step 4: Filter out the items that are already in the fridge
            filtered_missing_items = filter_missing_items(missing_items_list, fridge_items)
            
            # Step 5: Combine missing items with low-quantity items for the final shopping list
            shopping_list = create_final_shopping_list(filtered_missing_items, low_quantity_items)

            st.write("### Shopping List:")
            if shopping_list:
                st.write(shopping_list)
            else:
                st.write("No additional items needed!")

    # Button to generate another recipe
    st.button('Generate another recipe')