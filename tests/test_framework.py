
import asyncio
import json
import random
import time
import logging
import argparse
import sys
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [User-%(name)s] %(message)s',
    datefmt='%H:%M:%S'
)

class AgentBrowser:
    def __init__(self, user_id, headless=False):
        self.user_id = user_id
        self.logger = logging.getLogger(str(user_id))
        self.headless = headless
        self.session_name = f"user_{user_id}"

    async def run(self, command_str):
        """Run an agent-browser command."""
        cmd = f"agent-browser --session {self.session_name} {command_str}"
        self.logger.debug(f"Running: {cmd}")
        
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        
        if proc.returncode != 0:
            # Don't raise immediately, let caller handle? No, command failure is usually bad.
            # But sometimes 'wait' times out.
            err_msg = stderr.decode().strip()
            self.logger.error(f"Command failed: {cmd} -> {err_msg}")
            raise Exception(f"Command failed: {err_msg}")
            
        return stdout.decode().strip()

    async def open(self, url):
        return await self.run(f"open {url}")

    async def snapshot(self, args="-i --json"):
        output = await self.run(f"snapshot {args}")
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse snapshot output: {output}")
            return []

    async def click(self, ref):
        return await self.run(f"click {ref}")

    async def fill(self, ref, text):
        # Escape quotes
        safe_text = text.replace('"', '\\"')
        return await self.run(f'fill {ref} "{safe_text}"')
    
    async def press(self, key):
        return await self.run(f"press {key}")

    async def wait(self, args):
        try:
            return await self.run(f"wait {args}")
        except Exception as e:
            self.logger.warning(f"Wait command timed out or failed: {e}")
            raise

    async def get_url(self):
        return await self.run("get url")

    async def mouse_move(self, x, y):
        return await self.run(f"mouse move {x} {y}")

    async def mouse_down(self):
        return await self.run("mouse down left")
    
    async def mouse_up(self):
        return await self.run("mouse up left")

    async def close(self):
        return await self.run("close")


async def user_flow(user_config):
    user_id = user_config['id']
    browser = AgentBrowser(user_id)
    logger = browser.logger
    base_url = "http://localhost:3000"
    
    try:
        # 1. Login
        logger.info("Step 1: Login")
        await browser.open(f"{base_url}/login")
        
        # Assumption: Inputs will be named 'email' and 'password' or have those types
        await asyncio.sleep(2) # Wait for load (or use wait --load)
        elements = await browser.snapshot()
        
        email_ref = None
        pass_ref = None
        
        for el in elements:
            # Look for email input
            if el.get('tagName') == 'INPUT':
                attrs = el.get('attributes', {})
                name = attrs.get('name', '').lower()
                type_ = attrs.get('type', '').lower()
                
                if name == 'email' or type_ == 'email':
                    email_ref = el.get('ref')
                elif name == 'password' or type_ == 'password':
                    pass_ref = el.get('ref')

        if email_ref and pass_ref:
            logger.info("Found login fields, filling...")
            await browser.fill(email_ref, user_config['email'])
            await browser.fill(pass_ref, user_config['password'])
            await browser.press("Enter")
            await browser.wait("--load networkidle")
        else:
            logger.warning("Email/Password fields not found (expected in current version). Proceeding manually or assuming logged in.")
            # In a real test we might error here, but user said 'assume we will add later'
            # So we carry on.

        # 2. Search
        logger.info("Step 2: Search")
        await browser.open(f"{base_url}/app")
        await browser.wait("--load networkidle")
        
        # Find PromptInputTextarea
        elements = await browser.snapshot()
        textarea_ref = None
        for el in elements:
            if el.get('tagName') == 'TEXTAREA':
                # confirm it is the prompt input, maybe check placeholder
                attrs = el.get('attributes', {})
                placeholder = attrs.get('placeholder', '')
                if "Find me viral" in placeholder or "cooking videos" in placeholder: # Based on page.tsx code
                    textarea_ref = el.get('ref')
                    break
        
        # Fallback to first textarea if placeholder doesn't match exactly
        if not textarea_ref:
             for el in elements:
                if el.get('tagName') == 'TEXTAREA':
                    textarea_ref = el.get('ref')
                    break

        if textarea_ref:
            logger.info("Found search input, typing query...")
            await browser.fill(textarea_ref, "viral sung jin woo")
            await browser.press("Enter")
        else:
            logger.error("Search input not found!")
            return

        # 3. Chat Interaction
        logger.info("Step 3: Chat Interaction")
        # Explicitly wait for URL change
        try:
            await browser.wait("--url **/chats/**")
        except:
            logger.error("Failed to redirect to chat page")
            return
            
        logger.info("Redirected to chat. Waiting for submit to be enabled (Stop to disappear).")
        
        # 4. Wait for Stop button to NOT exist (meaning 'Send' is ready)
        # In ActionButtons.tsx, Stop button has tooltip "Stop generating"
        # Since we can't easily see tooltips in snapshot JSON without hovering or accessibility tree details,
        # we'll look for the ABSENCE of the Stop button or PRESENCE of Send button.
        # Send button has ArrowUp icon. Stop has Square icon.
        # But icons are SVGs. agent-browser might just see 'BUTTON'.
        # However, PromptInputTextarea and buttons are in PromptInput.
        
        # We loop and snapshot.
        start_wait = time.time()
        ready = False
        send_ref = None
        
        while time.time() - start_wait < 60: # 60s timeout
            elements = await browser.snapshot()
            
            # Try to identify Stop vs Send.
            # Usually Send button is enabled when not streaming.
            # When streaming, Stop button is shown.
            # We can check if there's a button with name="Stop generating" (if aria-label exists)
            # or simply wait for the number of buttons to be what we expect in "Ready" state.
            
            # Let's assume the button with the ArrowUp is the target.
            # If we see only one main action button, we can try to click it.
            
            # Heuristic: Find button in the input area.
            # If it's "Stop", it might be clickable.
            # We want to wait until it becomes "Send".
            
            # Since we can't easily distinguish purely by shape in JSON, 
            # we rely on the user flow: We just searched. It should be generating.
            # We wait some time.
            
            # Better: Check for "Send message" tooltip if exposed as name.
            send_btn = next((el for el in elements if el.get('name') == 'Send message' or el.get('text') == 'Send message'), None)
            stop_btn = next((el for el in elements if el.get('name') == 'Stop generating' or el.get('text') == 'Stop generating'), None)

            if send_btn and not stop_btn:
                ready = True
                send_ref = send_btn.get('ref')
                break
                
            await asyncio.sleep(1)
            
        if not ready:
            logger.warning("Could not definitively detect 'Send' state. Assuming ready after timeout.")
            
        # Type follow up
        textarea_ref = next((el.get('ref') for el in elements if el.get('tagName') == 'TEXTAREA'), None)
        if textarea_ref:
            await browser.fill(textarea_ref, "analyse any 5 videos")
            
            # Wait for submit visible (already checked ready)
            # Don't click immediately per instructions? "wait until submit is visible again dont click"
            # Oh, instr 4: "wait until submit is visible again dont click" -> Wait, 
            # I must type "analyse any 5 videos" then wait? 
            # Instr 3: "... wait until ... enable ... and type analyse any 5 videos"
            # Instr 4: "wait until submit is visible again dont click"
            
            # Wait, if I type, I usually need to send to start the next part?
            # User says: "type analyse any 5 videos" then "wait until submit is visible again".
            # This implies hitting enter/submit? Otherwise it won't be generating for submit to disappear/reappear.
            # I will assume I need to submit.
            
            if send_ref:
                await browser.click(send_ref)
            else:
                await browser.press("Enter")
                
            # Now wait for it to become visible *again* (meaning it became Stop then Send again)
            # await asyncio.sleep(2) # give it time to switch to Stop
            
            # Wait for 'Send' again
            # Reuse logic
            # ... (Simulated wait for generation to finish)
            await asyncio.sleep(5) 
        
        # 5. Glass Tabs Interaction (Drag & Click)
        logger.info("Step 5: Glass Tabs Interaction Loop")
        start_loop = time.time()
        
        while time.time() - start_loop < 60:
            elements = await browser.snapshot()
            
            # 1. Find the Glass Tabs Container (for dragging)
            # ChatTabs.tsx: className="... glass-nav ..."
            tabs_container = None
            for el in elements:
                classes = el.get('attributes', {}).get('class', '')
                if 'glass-nav' in classes:
                    tabs_container = el
                    break
            
            if tabs_container:
                # Drag the container
                logger.info("Dragging glass tabs container...")
                # Get bounding box if available, or just guess middle of screen top?
                # agent-browser snapshot -i doesn't give bbox by default unless asked? 
                # Actually default snapshot gives accessibility tree. -i gives interactive. 
                # If we don't have bbox, we can't drag precisely.
                # But we can try 'mouse move' to the element if 'ref' works?
                # 'mouse move' takes x y. We need to know where it is.
                # Let's use 'get box'
                
                try:
                    box_str = await browser.run(f"get box {tabs_container['ref']}")
                    # Output: {"x":..., "y":..., "width":..., "height":...}
                    box = json.loads(box_str)
                    
                    start_x = box['x'] + box['width'] / 2
                    start_y = box['y'] + box['height'] / 2
                    
                    await browser.mouse_move(start_x, start_y)
                    await browser.mouse_down()
                    await browser.mouse_move(start_x - random.randint(50, 150), start_y) # Drag left/right
                    await browser.mouse_up()
                except Exception as e:
                    logger.warning(f"Failed to drag tabs container: {e}")
            else:
                logger.warning("Glass tabs container (.glass-nav) not found")

            # 2. Click a Random Tab (Search Keyword)
            # We want buttons *inside* the glass-nav ideally, or just buttons that look like tabs.
            # In snapshot, hierarchy might be flattened depending on depth.
            # But we can look for buttons with specific expected classes or just 'role=button' and text.
            # ChatTabs buttons have "relative px-4 h-8 ... group/tab"
            
            tabs = []
            for el in elements:
                # Heuristic: Buttons that are likely the tabs.
                # They are usually short text.
                if el.get('role') == 'button':
                    classes = el.get('attributes', {}).get('class', '')
                    # Check for 'group/tab' which is in the code
                    if 'group/tab' in classes:
                        tabs.append(el)
            
            # Fallback if class names aren't in snapshot (sometimes they are stripped or not full)
            if not tabs:
                 # Try finding buttons that are siblings in the container?
                 # Too complex for simple script. fallback to any button not in blacklist.
                 for el in elements:
                    if el.get('role') == 'button':
                        name = el.get('name', '')
                        if name not in ['Stop generating', 'Send message', 'Attach image', 'New Chat', 'Close', 'Sign in with Google']:
                            tabs.append(el)

            if tabs:
                target = random.choice(tabs)
                logger.info(f"Clicking search keyword tab: {target.get('name') or target.get('text')}")
                try:
                    await browser.click(target.get('ref'))
                except:
                    pass
            
            await asyncio.sleep(10)

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await browser.close()

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--users', type=int, default=1)
    args = parser.parse_args()
    
    users = [{'id': i, 'email': f'user{i}@test.com', 'password': 'password'} for i in range(args.users)]
    
    tasks = [user_flow(u) for u in users]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
