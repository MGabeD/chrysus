from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

load_dotenv()

gemini_2 = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0,
    api_key=os.getenv("GOOGLE_API_KEY"),
)

gemini_2_5 = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    thinking_budget=1024,
    include_thoughts=False,
    api_key=os.getenv("GOOGLE_API_KEY"),
)

