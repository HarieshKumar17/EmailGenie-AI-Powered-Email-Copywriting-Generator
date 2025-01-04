import streamlit as st
import pandas as pd
from groq import Groq
import resend
from hubspot import HubSpot
import matplotlib.pyplot as plt
import os
import logging
from dotenv import load_dotenv
import sqlite3
import json
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize API clients
try:
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    resend.api_key = os.getenv("RESEND_API_KEY")
    hubspot_client = HubSpot(api_key=os.getenv("HUBSPOT_API_KEY"))
    logger.info("API clients initialized successfully")
except Exception as e:
    logger.error(f"Error initializing API clients: {str(e)}")
    st.error(f"Error initializing API clients. Please check your API keys and try again. Error: {str(e)}")

def generate_email(email_purpose, recipient_name, recipient_company, recipient_designation, industry, target_audience, background, sender_name, sender_company):
    try:
        prompt = f"""You are EmailGenie, an AI assistant specialized in crafting personalized cold outreach emails. Your task is to create an engaging and professional email based on the following information:
                Sender's Name: {sender_name}
                Sender's Company/Role: {sender_company}
                Recipient's Name: {recipient_name}
                Recipient's Company/Role: {recipient_company} ({recipient_designation})
                Industry: {industry}
                Purpose of Outreach: {email_purpose}
                Key Points to Include:
                - Target Audience: {target_audience}
                - Sender's Background: {background}
                Please generate a personalized email that is concise, engaging, and tailored to the recipient. The email should have a clear subject line and a well-structured body.
                Respond with a JSON object containing two fields:
                1. "subject": The subject line of the email
                2. "body": The body of the email
                """

        chat_completion = groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gemma2-9b-it",
            temperature=0,
            max_tokens=None,
            response_format={"type": "json_object"}
        )

        response = json.loads(chat_completion.choices[0].message.content)
        subject = response["subject"]
        body = response["body"]

        logger.info(f"Email generated successfully for {recipient_name} from {recipient_company}")
        return subject, body

    except Exception as e:
        logger.error(f"Error generating email: {str(e)}")
        return "Error generating email", "Please try again."
    

def create_local_db():
    conn = sqlite3.connect('email_genie.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS email_templates
                 (id INTEGER PRIMARY KEY, name TEXT, content TEXT, profile TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sent_emails
                 (id INTEGER PRIMARY KEY, recipient TEXT, subject TEXT, content TEXT, sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_email_template(name, content, profile):
    conn = sqlite3.connect('email_genie.db')
    c = conn.cursor()
    c.execute("INSERT INTO email_templates (name, content, profile) VALUES (?, ?, ?)", (name, content, json.dumps(profile)))
    conn.commit()
    conn.close()

def load_email_templates():
    conn = sqlite3.connect('email_genie.db')
    c = conn.cursor()
    c.execute("SELECT name, content, profile FROM email_templates")
    templates = c.fetchall()
    conn.close()
    return templates



def send_email(from_email: str, to_email: str, subject: str, body: str) -> Dict:
    try:
        params: resend.Emails.SendParams = {
            "from": "Acme <onboarding@resend.dev>",
            "to": "harryjakes17@gmail.com",
            #"to": [to_email],
            "subject": subject,
            "html": body,
        }
        email = resend.Emails.send(params)
        logger.info(f"Email sent successfully to {to_email}")
        return {"message": "Email sent successfully", "email_id": email["id"]}
    except Exception as e:
        logger.error(f"Error sending email: {str(e)}")
        return {"message": f"Failed to send email: {str(e)}"}

def update_crm(recipient_name, recipient_company, recipient_email, email_content):
    try:
        # Update HubSpot
        hubspot_client.crm.contacts.basic_api.create(
            properties={
                "email": recipient_email,
                "lastname": recipient_name,
                "company": recipient_company,
                "notes": f"Sent email: {email_content[:100]}..."
            }
        )
        
        # Update local DB
        conn = sqlite3.connect('email_genie.db')
        c = conn.cursor()
        c.execute("INSERT INTO sent_emails (recipient, subject, content) VALUES (?, ?, ?)", 
                  (recipient_email, "Your Subject Here", email_content))
        conn.commit()
        conn.close()
        
        logger.info(f"CRM updated for {recipient_name} from {recipient_company}")
    except Exception as e:
        logger.error(f"Error updating CRM: {str(e)}")

def load_profiles():
    try:
        profiles = pd.read_excel("data/user_profiles.xlsx")
        if profiles.empty or "Profile Name" not in profiles.columns:
            return pd.DataFrame(columns=["Profile Name", "Industry", "Target Audience", "Background", "Sender Name", "Sender Company", "Sender Email"])
        return profiles
    except FileNotFoundError:
        return pd.DataFrame(columns=["Profile Name", "Industry", "Target Audience", "Background", "Sender Name", "Sender Company", "Sender Email"])

def save_profile(profile_name, industry, target_audience, background, sender_name, sender_company, sender_email):
    profiles = load_profiles()
    new_profile = pd.DataFrame({
        "Profile Name": [profile_name],
        "Industry": [industry],
        "Target Audience": [target_audience],
        "Background": [background],
        "Sender Name": [sender_name],
        "Sender Company": [sender_company],
        "Sender Email": [sender_email]
    })
    profiles = pd.concat([profiles, new_profile], ignore_index=True)
    os.makedirs("data", exist_ok=True)  # Ensure the data directory exists
    profiles.to_excel("data/user_profiles.xlsx", index=False)
    st.success("Profile saved successfully!")

def user_profile_setup():
    st.header("User Profile Setup")

    # Create new profile
    st.subheader("Create New Profile")
    profile_name = st.text_input("Profile Name")
    industry = st.text_input("Industry")
    target_audience = st.text_input("Target Audience")
    background = st.text_area("Personal/Company Background")
    sender_name = st.text_input("Your Name")
    sender_company = st.text_input("Your Company/Role")
    sender_email = st.text_input("Your Email")

    if st.button("Save Profile"):
        if profile_name and industry and target_audience and background and sender_name and sender_company and sender_email:
            save_profile(profile_name, industry, target_audience, background, sender_name, sender_company, sender_email)
        else:
            st.error("Please fill in all fields before saving the profile.")

    # View existing profiles
    st.subheader("Existing Profiles")
    profiles = load_profiles()
    if not profiles.empty:
        for _, profile in profiles.iterrows():
            with st.expander(f"Profile: {profile['Profile Name']}"):
                st.write(f"Industry: {profile['Industry']}")
                st.write(f"Target Audience: {profile['Target Audience']}")
                st.write(f"Background: {profile['Background']}")
                st.write(f"Sender Name: {profile['Sender Name']}")
                st.write(f"Sender Company/Role: {profile['Sender Company']}")
                st.write(f"Sender Email: {profile['Sender Email']}")
                if st.button("Delete Profile", key=f"delete_{profile['Profile Name']}"):
                    profiles = profiles[profiles['Profile Name'] != profile['Profile Name']]
                    profiles.to_excel("data/user_profiles.xlsx", index=False)
                    st.success(f"Profile '{profile['Profile Name']}' deleted successfully.")
                    st.experimental_rerun()
    else:
        st.info("No profiles found. Create a new profile above.")

def generate_email_tab():
    st.header("Generate Email")
    
    profiles = load_profiles()
    if not profiles.empty and "Profile Name" in profiles.columns:
        profile_names = profiles["Profile Name"].tolist()
        selected_profile_name = st.selectbox("Select Profile", [""] + profile_names)
        if selected_profile_name:
            selected_profile = profiles[profiles["Profile Name"] == selected_profile_name].iloc[0]
        else:
            selected_profile = None
    else:
        st.warning("No profiles found. Please create a new profile.")
        selected_profile = None
    
    email_purpose = st.selectbox("Email Purpose", ["Sales Pitch", "Job Application", "Service Offer", "Partnership Proposal", "Event Invitation"])
    recipient_name = st.text_input("Recipient Name")
    recipient_company = st.text_input("Recipient Company")
    recipient_designation = st.text_input("Recipient Designation")
    recipient_email = st.text_input("Recipient Email")

    if st.button("Generate Email", key="generate_email_button"):
        if selected_profile is not None:
            industry = selected_profile["Industry"]
            target_audience = selected_profile["Target Audience"]
            background = selected_profile["Background"]
            sender_name = selected_profile["Sender Name"]
            sender_company = selected_profile["Sender Company"]
            sender_email = selected_profile["Sender Email"]
            
            subject, body = generate_email(email_purpose, recipient_name, recipient_company, recipient_designation, industry, target_audience, background, sender_name, sender_company)
            
            st.session_state.preview_recipient = recipient_email
            st.session_state.preview_subject = subject
            st.session_state.preview_content = body
            st.session_state.sender_email = sender_email
            st.session_state.sender_name = sender_name
            st.session_state.sender_company = sender_company
            st.session_state.active_tab = "Email Preview"
            st.rerun()  # Changed from st.experimental_rerun() to st.rerun()
        else:
            st.error("Please select a profile before generating an email.")

def email_preview_tab():
    st.header("Email Preview")
    sender_name = st.session_state.get('sender_name', '')
    sender_company = st.session_state.get('sender_company', '')
    sender_email = st.text_input("From", value=f"{sender_name} ({sender_company}) <{st.session_state.get('sender_email', '')}>")
    recipient_email = st.text_input("To", key="preview_recipient", value=st.session_state.preview_recipient)
    subject = st.text_input("Subject", key="preview_subject", value=st.session_state.preview_subject)
    email_content = st.text_area("Email Body", height=300, key="preview_content", value=st.session_state.preview_content)

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Send Email", key="send_preview_email_button"):
            result = send_email(sender_email, recipient_email, subject, email_content)
            if "email_id" in result:
                st.success(f"Email sent successfully! Email ID: {result['email_id']}")
                #update_crm(recipient_name, recipient_company, recipient_email, email_content)
            else:
                st.error(result["message"])
    
    
def main():
    st.set_page_config(layout="wide")
    st.title("EmailGenie - AI-Powered Email Copywriting Generator")

    create_local_db()

    if 'preview_recipient' not in st.session_state:
        st.session_state.preview_recipient = ""
    if 'preview_subject' not in st.session_state:
        st.session_state.preview_subject = ""
    if 'preview_content' not in st.session_state:
        st.session_state.preview_content = ""
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "User Profile Setup"

    tabs = ["User Profile Setup", "Generate Email", "Email Preview"]
    st.session_state.active_tab = st.radio("Navigation", tabs, index=tabs.index(st.session_state.active_tab))

    if st.session_state.active_tab == "User Profile Setup":
        user_profile_setup()
    elif st.session_state.active_tab == "Generate Email":
        generate_email_tab()
    elif st.session_state.active_tab == "Email Preview":
        email_preview_tab()

if __name__ == "__main__":
    main()
