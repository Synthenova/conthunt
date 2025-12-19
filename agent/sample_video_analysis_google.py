import asyncio
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

# Initialize the model
llm = ChatGoogleGenerativeAI(
    model="gemini-3-flash-preview",
    temperature=0.7,
    project='conthunt-dev',
    vertexai=True
)

async def main():
    # Build the message with the video URI
    message = HumanMessage(
        content=[
            {"type": "text", "text": "Please analyze the content of this video and summarize what happens."},
            {
                "type": "media",
                "file_uri": "gs://conthunt-dev-media/media/instagram/3663637157466504641/video/a744572a9c55727d13aa11cb6aeff14382af038f3908ea83c8883b371fb5a4a9.mp4",
                "mime_type": "video/mp4",
            }
        ]
    )

    # Use .astream() to stream chunks asynchronously
    print("Streaming response: ", end="", flush=True)
    
    async for chunk in llm.astream([message]):
        # Print each chunk as it arrives without a newline
        print(chunk.content, end="", flush=True)
    
    print() # Final newline

if __name__ == "__main__":
    asyncio.run(main())