import os

from groq import Groq

MODEL_NAME = "llama-3.3-70b-versatile"


def _get_client():
    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing. Please set it in .env")
    return Groq(api_key=api_key)


def chat_with_agent(user_message, conversation_history):
    system_prompt = (
        "You are a business onboarding assistant helping set up an AI "
        "email auto-responder. Your job is to learn everything about the "
        "user's business so you can reply to customer enquiries on their "
        "behalf. Ask about: what services or products they offer, pricing "
        "and packages, key features and benefits, turnaround times, "
        "frequently asked questions, preferred tone of voice (formal or "
        "friendly), contact details, and anything else relevant. Once you "
        "have enough information, summarize the complete business profile "
        "clearly. Be conversational and ask one or two questions at a time."
    )

    history = conversation_history[:] if conversation_history else []
    history.append({"role": "user", "content": user_message})

    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "system", "content": system_prompt}] + history,
        temperature=0.5,
    )

    reply = response.choices[0].message.content.strip()
    history.append({"role": "assistant", "content": reply})
    return {"reply": reply, "updated_history": history}


def extract_business_summary(conversation_history):
    system_prompt = (
        "Based on the conversation history provided, extract and summarize "
        "all business information into a clean structured profile. Include: "
        "business name, services offered, pricing, features, turnaround "
        "times, FAQs, tone of voice, and contact details. Format it clearly "
        "so it can be used as context for replying to customer emails."
    )

    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Conversation history: {conversation_history}"},
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content.strip()


def generate_email_reply(business_knowledge, sender_name, sender_email, email_subject, email_body):
    system_prompt = (
        "You are an AI email assistant for a business. Using the business "
        "knowledge provided, write a professional and helpful reply to the "
        "customer enquiry. Match the tone described in the business knowledge."
        " Be specific — reference their actual question. Do not make up "
        "information not in the business knowledge. End with a friendly "
        "call to action. Do not include a subject line, just the email body. "
        "Sign off with the business name from the knowledge base."
    )
    user_message = (
        f"Business Knowledge: {business_knowledge}\n\n"
        "New enquiry received:\n"
        f"From: {sender_name} <{sender_email}>\n"
        f"Subject: {email_subject}\n"
        f"Message: {email_body}\n\n"
        "Write a reply to this enquiry."
    )

    client = _get_client()
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        temperature=0.4,
    )
    return response.choices[0].message.content.strip()