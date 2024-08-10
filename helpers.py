from langchain_community.document_loaders import PyMuPDFLoader
from langchain_openai import ChatOpenAI

def validate_pdf_file(file_path):
    # Check the file extension
    if file_path.lower().endswith('.pdf'):
        return "File is a PDF based on its extension."

def extract_pdf_text(file_path):
    # Extract text from PDF
    loader = PyMuPDFLoader(file_path)
    data = loader.load()
    text_str = ''
    for d in data:
        text_str = text_str + d.page_content
    return text_str

def validate_cv(cv_text):
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        max_tokens=1,
        timeout=None,
        max_retries=2,
        api_key="sk-whatsapp-m4BOtm3wYwyDvL52JJgAT3BlbkFJf2jH4gz7Uck5yCaco1g5",  # if you prefer to pass api key in directly instaed of using env vars
    )

    cv_validation_prompt = f"""
I have a CV with the following content: {cv_text}

Please validate the CV based on the following criteria:

1. Does it contain personal information (name, contact details)?
2. Are there sections for education or work experience?
3. Is the CV properly formatted with headings?

Only return `1` if the CV meets all the criteria, and `0` if it does not. If any of the criteria are not met, return `0`."""

    messages = [
        (
            "system",
            "You are a helpful assistant.",
        ),
        ("human", cv_validation_prompt),
    ]

    ai_msg = llm.invoke(messages)

    if ai_msg.content == "1":
        return True
    else:
        return False

def validate_job(job_text):
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0,
        max_tokens=1,
        timeout=None,
        max_retries=2,
        api_key="sk-whatsapp-m4BOtm3wYwyDvL52JJgAT3BlbkFJf2jH4gz7Uck5yCaco1g5",  # if you prefer to pass api key in directly instaed of using env vars
    )

    job_validation_prompt = f"""
I have received the following job details: {job_text}

Please validate these details based on the following criteria:

1. Is there a clear mention of a job or position in the details? For example, it should specify the job title or role required.

Only return `1` if the job meets all the criteria, and `0` if it does not. If any of the criteria are not met, return `0`."""

    messages = [
        (
            "system",
            "You are a helpful assistant.",
        ),
        ("human", job_validation_prompt),
    ]

    ai_msg = llm.invoke(messages)

    if ai_msg.content == "1":
        return True
    else:
        return False

def generate_email_draft(cv_text, job_text):
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key="sk-whatsapp-m4BOtm3wYwyDvL52JJgAT3BlbkFJf2jH4gz7Uck5yCaco1g5",  # if you prefer to pass api key in directly instaed of using env vars
    )

    generate_email_draft_prompt = f"""
I need to generate a professional email using the following information:

1. **CV Content**: {cv_text}
2. **Job Details**: {job_text}

Please create an email that includes:

- A formal greeting.
- An introduction that references the CV.
- A mention of the job details and why the candidate is a good fit for the position.
- A closing statement expressing interest in discussing the opportunity further.
- A professional signature.

Ensure the email is well-structured, clear, and tailored to the job details provided.

Generate the email in a professional and engaging tone."""

    messages = [
        (
            "system",
            "You are a helpful assistant.",
        ),
        ("human", generate_email_draft_prompt),
    ]

    ai_msg = llm.invoke(messages)

    return ai_msg.content

def adjust_email_draft(email_text, user_prompt):
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key="sk-whatsapp-m4BOtm3wYwyDvL52JJgAT3BlbkFJf2jH4gz7Uck5yCaco1g5",  # if you prefer to pass api key in directly instaed of using env vars
    )

    messages = [
        (
            "system",
            "You are a helpful assistant.",
        ),
        ("ai", email_text),
        ("human", user_prompt),
    ]

    ai_msg = llm.invoke(messages)

    return ai_msg.content