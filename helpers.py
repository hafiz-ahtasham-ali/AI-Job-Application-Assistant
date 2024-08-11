from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.callbacks import get_openai_callback
from langchain_openai import ChatOpenAI
import base64
import requests

gpt_model = 'gpt-4o-mini'
# openai_api_key = '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'
openai_api_key = 'sk-whatsapp-m4BOtm3wYwyDvL52JJgAT3BlbkFJf2jH4gz7Uck5yCaco1g5'

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
        model=gpt_model,
        temperature=0,
        max_tokens=1,
        timeout=None,
        max_retries=2,
        api_key=openai_api_key,  # if you prefer to pass api key in directly instaed of using env vars
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

    with get_openai_callback() as cb:
        ai_msg = llm.invoke(messages)
        if ai_msg.content == "1":
            return cb.total_cost
        else:
            return False

def validate_job(job_text):
    llm = ChatOpenAI(
        model=gpt_model,
        temperature=0,
        max_tokens=1,
        timeout=None,
        max_retries=2,
        api_key=openai_api_key,  # if you prefer to pass api key in directly instaed of using env vars
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

    with get_openai_callback() as cb:
        ai_msg = llm.invoke(messages)
        if ai_msg.content == "1":
            return cb.total_cost
        else:
            return False

def create_draft_email(cv_text, job_text):
    llm = ChatOpenAI(
        model=gpt_model,
        temperature=0.3,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=openai_api_key,  # if you prefer to pass api key in directly instaed of using env vars
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

    with get_openai_callback() as cb:
        ai_msg = llm.invoke(messages)
        return {'content': ai_msg.content, 'cost': cb.total_cost}

def adjust_email_draft(email_text, user_prompt):
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.3,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=openai_api_key,  # if you prefer to pass api key in directly instaed of using env vars
    )

    messages = [
        (
            "system",
            "You are a helpful assistant.",
        ),
        ("ai", email_text),
        ("human", user_prompt),
    ]

    with get_openai_callback() as cb:
        ai_msg = llm.invoke(messages)
        return {'content': ai_msg.content, 'cost': cb.total_cost}

def extract_text_from_img(image_path):
    # Function to encode the image
    def encode_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    # Getting the base64 string
    base64_image = encode_image(image_path)
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {openai_api_key}"
    }
    payload = {
    "model": gpt_model,
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": "Convert image to text"
            },
            {
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 300
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    prompt_cost = (response.json()["usage"]["prompt_tokens"] * 0.15) / 1000000
    completion_cost = (response.json()["usage"]["completion_tokens"] * 0.6) / 1000000
    total_cost = prompt_cost + completion_cost
    return {'content': response.json()["choices"][0]["message"]["content"], 'cost': total_cost}