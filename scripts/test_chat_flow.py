import asyncio
import uuid
import httpx
import json
import sys

# Configuration
API_URL = "http://localhost:8000/v1"

async def test_chat_flow(token: str, existing_chat_id: str = None):
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        chat_id = existing_chat_id
        
        if not chat_id:
            # 1. Create Chat
            print(f"\n--- Creating Chat ---")
            try:
                resp = await client.post(
                    f"{API_URL}/chats/", 
                    json={"title": "Test Chat Integration"}, 
                    headers=headers
                )
                resp.raise_for_status()
                chat = resp.json()
                chat_id = chat["id"]
                print(f"Chat Created: {chat_id} (Thread: {chat['thread_id']})")
            except Exception as e:
                print(f"Failed to create chat: {e}")
                return
        else:
             print(f"\n--- Using Existing Chat: {chat_id} ---")

        # 2. Send Message
        print(f"\n--- Sending Message ---")
        msg = "Tell me a long story about a space dragon. Make it at least 5 paragraphs."
        try:
            resp = await client.post(
                f"{API_URL}/chats/{chat_id}/send",
                json={"message": msg},
                headers=headers
            )
            resp.raise_for_status()
            print("Message sent successfully (Job Enqueued)")
        except Exception as e:
            print(f"Failed to send message: {e}")
            return

        # 3. Stream with Multiple Interruptions (Stress Test)
        print(f"\n--- Streaming (Disconnecting 5 times) ---")
        
        last_received_id = None
        full_content = ""
        is_done = False
        
        # We will attempt 5 reconnections
        for attempt in range(1, 6):
            if is_done: break
            
            print(f"\n[Attempt {attempt}/5] Connecting (Last-ID: {last_received_id})...")
            
            reconnect_headers = headers.copy()
            if last_received_id:
                reconnect_headers["Last-Event-ID"] = last_received_id
            
            chunks_read_this_turn = 0
            
            try:
                async with client.stream("GET", f"{API_URL}/chats/{chat_id}/stream", headers=reconnect_headers) as stream:
                    async for line in stream.aiter_lines():
                        if not line: continue
                        
                        # Capture ID
                        if line.startswith("id: "):
                            last_received_id = line[4:].strip()
                            
                        # Capture Data
                        if line.startswith("data: "):
                            data_str = line[6:]
                            
                            # Check for done
                            if '"type": "done"' in data_str:
                                print(f"  -> Stream DONE received.")
                                is_done = True
                                break
                            
                            # Parse content
                            try:
                                data = json.loads(data_str)
                                if data.get("type") == "content_delta":
                                    content = data.get("content", "")
                                    full_content += content
                                    # Print a dot for progress
                                    print(".", end="", flush=True)
                            except:
                                pass
                                
                            chunks_read_this_turn += 1
                            
                            # Disconnect condition: Read ~5 chunks then break (unless it's the 5th attempt, then finish)
                            if attempt < 5 and chunks_read_this_turn >= 5:
                                print(f"\n  -> Interrupting after {chunks_read_this_turn} chunks. (Last ID: {last_received_id})")
                                break
                                
            except Exception as e:
                print(f"  -> Connection error: {e}")
        
        # If not done after 5 interruptions, finish it off
        if not is_done:
            print(f"\n\n[Finalizing] Connecting to finish stream...")
            reconnect_headers = headers.copy()
            if last_received_id:
                reconnect_headers["Last-Event-ID"] = last_received_id
                
            try:
                async with client.stream("GET", f"{API_URL}/chats/{chat_id}/stream", headers=reconnect_headers) as stream:
                    async for line in stream.aiter_lines():
                        if line.startswith("data: "):
                             data_str = line[6:]
                             if '"type": "done"' in data_str:
                                 is_done = True
                                 break
                             try:
                                data = json.loads(data_str)
                                if data.get("type") == "content_delta":
                                    full_content += data.get("content", "")
                                    print(".", end="", flush=True)
                             except: pass
            except Exception as e:
                print(f"Final error: {e}")

        print("\n\n--- Final Assembled Content ---")
        print(full_content)
        print("-------------------------------")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_chat_flow.py <FIREBASE_TOKEN> [CHAT_ID]")
    else:
        chat_id_arg = sys.argv[2] if len(sys.argv) > 2 else None
        asyncio.run(test_chat_flow(sys.argv[1], chat_id_arg))
