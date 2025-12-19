import os
import sys
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

def analyze_video(video_url: str):
    """
    Analyzes a video using ChatOpenAI with OpenRouter and Gemini 2.0 Flash.
    """
    
    # Check for API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Error: OPENAI_API_KEY not found in environment variables.")
        print("Please add it to your .env file.")
        return

    # Configure ChatOpenAI for OpenRouter    
    llm = ChatOpenAI(
        model="google/gemini-3-flash-preview",
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0,
    )

    # Construct the message payload according to the specified schema
    message = HumanMessage(
        content=[
            {
                "type": "text", 
                "text": "Please analyze this video and describe what happens in it in detail."
            },
            {
                "type": "video_url",
                "video_url": video_url,
                # Optional fields from user schema:
                # "base64": "...",
                # "id": "...",
                # "mime_type": "video/mp4" 
            }
        ]
    )

    import requests
    import json

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please describe what's happening in this video."
                },
                {
                    "type": "video_url",
                    "video_url": {
                        "url": video_url
                    }
                }
            ]
        }
    ]

    payload = {
        "model": "google/gemini-3-flash-preview",
        "messages": messages
    }

    response = requests.post(url, headers=headers, json=payload)
    print(response.json())


    try:
        print(f"Analyzing video at: {video_url}")
        print(f"Using model: {llm.model_name}")
        
        response = llm.invoke([message])
        
        print("\n--- Analysis Result ---")
        print(response.content)
        
    except Exception as e:
        print(f"\nError during analysis: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/sample_video_analysis.py <video_url>")
        sys.exit(1)
        
    url = sys.argv[1]
    analyze_video(url)
