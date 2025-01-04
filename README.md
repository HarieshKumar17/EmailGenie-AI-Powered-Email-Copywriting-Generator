# EmailGenie-AI-Powered-Email-Copywriting-Generator

### Overview

EmailGenie is a sophisticated AI-powered email copywriting tool that leverages the Groq AI platform to generate personalized cold outreach emails. The system combines modern AI language models with professional email marketing best practices to create engaging, contextually relevant emails for various business purposes.

### Key Features

- **AI-Powered Email Generation**: Utilizes Groq's Gemma-2-9B model for intelligent email composition
- **Profile Management**: Custom user profile creation and management system
- **Multi-Purpose Templates**: Supports various email types (Sales, Job Applications, Partnerships, etc.)
- **Email Preview & Editing**: Real-time email preview and modification capabilities
- **Direct Email Integration**: Seamless sending via Resend API
- **CRM Integration**: HubSpot integration for contact management
- **Local Database**: SQLite storage for email templates and sending history

### Technical Architecture

### Technology Stack

- **Frontend**: Streamlit
- **AI Model**: Groq (Gemma-2-9B)
- **Email Service**: Resend
- **CRM**: HubSpot
- **Database**: SQLite
- **Data Processing**: Pandas
- **Environment Management**: Python-dotenv

### Core Components

1. **Profile Management System**
    
    ```python
    def user_profile_setup():
        # Handles profile creation and management
        # Stores sender information
        # Manages industry and background details
        
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
    
    ```
    
2. **Email Generation Engine**
    
    ```python
    def generate_email(email_purpose, recipient_name, recipient_company, recipient_designation, industry, target_audience, background, sender_name, sender_company):
        # AI-powered email content generation
        # Context-aware subject line creation
        # JSON response formatting
        
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
    
    ```
    
3. **Email Delivery System**
    
    ```python
    def send_email(from_email: str, to_email: str, subject: str, body: str) -> Dict:
        # Email sending via Resend API
        # Error handling and logging
        # Delivery confirmation
        
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
    
    ```
    
4. **CRM Integration**
    
    ```python
    def update_crm(recipient_name, recipient_company, recipient_email, email_content):
        # HubSpot contact creation/update
        # Email history tracking
        # Local database synchronization
        
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
    
    ```
    

### Installation and Setup

1. **Prerequisites**
    
    ```bash
    pip install -r requirements.txt
    
    ```
    
2. **Environment Variables(.env)**
    
    ```
    GROQ_API_KEY=your_groq_api_key
    RESEND_API_KEY=your_resend_api_key
    HUBSPOT_API_KEY=your_hubspot_api_key
    
    ```
    
3. **Requirements.txt**
    ```
    streamlit
    groq
    resend
    hubspot-api-client
    pandas
    python-dotenv
    sqlite3
    ```

### Usage Guide

1. **Profile Setup**
    - Create sender profiles
    - Define industry and target audience
    - Store background information
    - Manage multiple profiles
2. **Email Generation**
    - Select email purpose
    - Input recipient details
    - Choose sender profile
    - Generate AI-powered content
3. **Email Preview & Sending**
    - Review generated content
    - Edit subject and body
    - Send directly via platform
    - Track sending history

### Technical Implementation Details

### Database Schema

```sql
CREATE TABLE email_templates (
    id INTEGER PRIMARY KEY,
    name TEXT,
    content TEXT,
    profile TEXT
);

CREATE TABLE sent_emails (
    id INTEGER PRIMARY KEY,
    recipient TEXT,
    subject TEXT,
    content TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

```

### Email Generation Process

1. Profile Selection
2. Recipient Detail Input
3. AI Content Generation
4. Preview & Editing
5. Sending & Tracking

### Running the Chatbot
Run the Streamlit application with the following command:
    
    streamlit run app.py
    
### Contributing

Contributions are welcome! Please read our contributing guidelines and code of conduct before submitting pull requests.

### License

This project is licensed under the MIT License - see the LICENSE file for details.
