
import asyncio
import json
import random
import time
import logging
import argparse
import sys
import os
import re
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] [User-%(name)s] %(message)s',
    datefmt='%H:%M:%S'
)

class AgentBrowser:
    def __init__(self, user_id, headless=False):
        self.user_id = user_id
        self.logger = logging.getLogger(str(user_id))
        self.headless = False
        self.session_name = f"user_{user_id}"
        self.command_timeout = 180

    async def run(self, command_str):
        """Run an agent-browser command."""
        headed_flag = "--headed " if not self.headless else ""
        cmd = f"agent-browser {headed_flag}--session {self.session_name} {command_str}"
        self.logger.debug(f"Running: {cmd}")
        
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.command_timeout)
        except asyncio.TimeoutError:
            proc.kill()
            raise Exception(f"Command timed out after {self.command_timeout}s: {cmd}")
        
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
            data = json.loads(output)
            if isinstance(data, dict) and "data" in data:
                snapshot_text = data.get("data", {}).get("snapshot", "")
                parsed = []
                for line in snapshot_text.splitlines():
                    line = line.strip()
                    if not line.startswith("-"):
                        continue
                    ref_match = re.search(r"\[ref=(e\d+)\]", line)
                    if not ref_match:
                        continue
                    ref_id = ref_match.group(1)
                    role_match = re.search(r"-\s+([a-zA-Z]+)\b", line)
                    name_match = re.search(r"\"([^\"]+)\"", line)
                    parsed.append({
                        "ref": ref_id,
                        "role": role_match.group(1).lower() if role_match else "",
                        "name": name_match.group(1) if name_match else "",
                        "disabled": "[disabled]" in line,
                        "raw": line,
                    })
                return parsed
            return data
        except json.JSONDecodeError:
            self.logger.error(f"Failed to parse snapshot output: {output}")
            return []

    def _as_ref(self, ref):
        return ref if str(ref).startswith("@") else f"@{ref}"

    async def click(self, ref):
        return await self.run(f"click {self._as_ref(ref)}")

    async def fill(self, ref, text):
        # Escape quotes
        safe_text = text.replace('"', '\\"')
        return await self.run(f'fill {self._as_ref(ref)} "{safe_text}"')
    
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

    async def get_value(self, selector):
        return await self.run(f"get value {selector}")

    async def mouse_move(self, x, y):
        return await self.run(f"mouse move {x} {y}")

    async def mouse_down(self):
        return await self.run("mouse down left")
    
    async def mouse_up(self):
        return await self.run("mouse up left")

    async def close(self):
        return await self.run("close")

    async def save_screenshot(self, path):
        return await self.run(f"screenshot {path}")


async def user_flow(user_config, timestamp_dir, headless=True):
    user_id = user_config['id']
    browser = AgentBrowser(user_id, False)
    logger = browser.logger
    base_url = "https://dev.agent.conthunt.app"
    
    user_dir = os.path.join(timestamp_dir, browser.session_name)
    if timestamp_dir:
        os.makedirs(user_dir, exist_ok=True)

    async def capture(name):
        if timestamp_dir:
            try:
                path = os.path.join(user_dir, f"{name}.png")
                await browser.save_screenshot(path)
            except Exception as e:
                logger.error(f"Failed to save screenshot {name}: {e}")

    try:
        # 1. Login
        logger.info("Step 1: Login")
        await browser.open(f"{base_url}/login")
        
        # Assumption: Inputs will be named 'email' and 'password' or have those types
        await asyncio.sleep(2) # Wait for load (or use wait --load)
        elements = await browser.snapshot()

        email_button_ref = None
        for el in elements:
            if el.get('role') == 'button':
                name = (el.get('name') or el.get('text') or '').strip().lower()
                if name == 'sign in with email':
                    email_button_ref = el.get('ref')
                    break

        if email_button_ref:
            logger.info("Opening email sign-in form...")
            await browser.click(email_button_ref)
            await asyncio.sleep(1)
            elements = await browser.snapshot()
        
        email_ref = None
        pass_ref = None
        
        for el in elements:
            if el.get('role') == 'textbox':
                name = (el.get('name') or '').strip().lower()
                if name == 'email':
                    email_ref = el.get('ref')
                elif name == 'password':
                    pass_ref = el.get('ref')

        if email_ref and pass_ref:
            logger.info("Found login fields, filling...")
            email_value = ""
            pass_value = ""
            try:
                email_value = await browser.get_value('input[type="email"]')
                pass_value = await browser.get_value('input[type="password"]')
            except Exception as e:
                logger.warning(f"Autofill check failed; proceeding to fill: {e}")
            if not email_value:
                await browser.fill(email_ref, user_config['email'])
            if not pass_value:
                await browser.fill(pass_ref, user_config['password'])

            elements = await browser.snapshot()
            sign_in_ref = None
            for el in elements:
                if el.get('role') == 'button':
                    name = (el.get('name') or el.get('text') or '').strip().lower()
                    if name == 'sign in':
                        sign_in_ref = el.get('ref')
                        break

            if sign_in_ref:
                await browser.click(sign_in_ref)
            else:
                await browser.press("Enter")
        else:
            logger.warning("Email/Password fields not found (expected in current version). Proceeding manually or assuming logged in.")
            # In a real test we might error here, but user said 'assume we will add later'
            # So we carry on.

        login_ready = False
        start_wait = time.time()
        while time.time() - start_wait < 60:
            elements = await browser.snapshot()
            has_trending = any(
                el.get('role') == 'button'
                and (el.get('name') or '').strip().lower() == "trending fitness content"
                for el in elements
            )
            if has_trending:
                login_ready = True
                break
            await asyncio.sleep(1)

        if not login_ready:
            logger.error("Login did not complete (missing 'Trending fitness content' button).")
            return

        await capture("step_1")

        # 2. Search
        logger.info("Step 2: Search")
        await browser.open(f"{base_url}/app")
        
        elements = await browser.snapshot()
        trending_ref = None
        for el in elements:
            if el.get('role') == 'button' and (el.get('name') or '').strip().lower() == "trending fitness content":
                trending_ref = el.get('ref')
                break

        if trending_ref:
            logger.info("Clicking 'Trending fitness content' suggestion...")
            await browser.click(trending_ref)
            await asyncio.sleep(1)
        else:
            logger.error("Trending fitness content button not found!")
            return

        elements = await browser.snapshot()
        search_input_ref = next(
            (
                el.get('ref')
                for el in elements
                if el.get('role') == 'textbox'
                and (el.get('name') or '').strip().lower() == "find me viral cooking videos..."
            ),
            None,
        )
        if search_input_ref:
            logger.info("Focusing search input and submitting with Enter...")
            await browser.click(search_input_ref)
            await browser.press("Enter")
        else:
            logger.warning("Search input not found; falling back to Enter.")
            await browser.press("Enter")

        await capture("step_2")

        # 3. Chat Interaction
        logger.info("Step 3: Chat Interaction")
        # Explicitly wait for URL change (manual poll to allow longer wait)
        chat_url_found = False
        start_wait = time.time()
        while time.time() - start_wait < 60:
            try:
                current_url = await browser.get_url()
                if "/app/chats/" in current_url:
                    chat_url_found = True
                    break
            except Exception as e:
                logger.warning(f"URL check failed: {e}")
            await asyncio.sleep(1)

        if not chat_url_found:
            logger.error("Failed to redirect to chat page")
            return

        logger.info("Waiting for model selector and disabled send button...")
        start_wait = time.time()
        model_ready = False
        while time.time() - start_wait < 60:
            elements = await browser.snapshot()
            has_model_button = any(
                el.get('role') == 'button' and (el.get('name') or '').strip() == "Gemini 3 Flash"
                for el in elements
            )
            has_disabled_send = any(
                el.get('role') == 'button'
                and not (el.get('name') or '').strip()
                and el.get('disabled')
                for el in elements
            )
            if has_model_button and has_disabled_send:
                model_ready = True
                break
            await asyncio.sleep(10)

        if not model_ready:
            logger.warning("Model selector or disabled send button not detected; proceeding anyway.")

        message_ref = next(
            (
                el.get('ref')
                for el in elements
                if el.get('role') == 'textbox'
                and (el.get('name') or '').strip().lower() == "message agent..."
            ),
            None,
        )
        if message_ref:
            await browser.fill(message_ref, "retreive one search and analyse top 10 videos")
        else:
            logger.error("Message input not found.")
            return
            
        logger.info("Waiting for streaming to finish before follow up...")
        start_wait = time.time()
        send_ref = None

        while time.time() - start_wait < 180:
            elements = await browser.snapshot()
            send_btn = next(
                (el for el in elements if (el.get('name') or '').strip() == "Send message"),
                None,
            )
            stop_btn = next(
                (el for el in elements if (el.get('name') or '').strip() == "Stop generating"),
                None,
            )
            if send_btn and not stop_btn:
                send_ref = send_btn.get('ref')
                break
            await asyncio.sleep(1)

        if not send_ref:
            logger.error("Send button not ready after streaming.")
            return

        await browser.click(send_ref)
        logger.info("Follow up submitted.")
        elements = await browser.snapshot()
        excluded_names = {
            "rename chat",
            "new chat",
            "close",
            "load more",
            "thinking",
            "gemini 3 flash",
            "close chat",
            "send message",
            "stop generating",
        }
        start_index = next(
            (idx for idx, el in enumerate(elements) if (el.get('name') or '').strip().lower() == "rename chat"),
            None,
        )
        keyword_buttons = []
        if start_index is not None:
            for el in elements[start_index + 1:]:
                name = (el.get('name') or '').strip()
                lower_name = name.lower()
                if lower_name in {"new chat", "close", "thinking"}:
                    break
                if el.get('role') != 'button' or not name:
                    continue
                if lower_name in excluded_names or lower_name.startswith("remove "):
                    continue
                keyword_buttons.append(el)
        else:
            for el in elements:
                name = (el.get('name') or '').strip()
                lower_name = name.lower()
                if el.get('role') != 'button' or not name:
                    continue
                if lower_name in excluded_names or lower_name.startswith("remove "):
                    continue
                keyword_buttons.append(el)

        if len(keyword_buttons) < 6:
            logger.warning("Not enough keyword buttons found after follow up.")
        else:
            target_refs = [
                keyword_buttons[3].get('ref'),
                keyword_buttons[4].get('ref'),
                keyword_buttons[5].get('ref'),
            ]
            click_order = [0, 1, 2, 0, 1, 2]
            for idx in click_order:
                await browser.click(target_refs[idx])
                await asyncio.sleep(10)

        await capture("step_3")
        await asyncio.sleep(120)
        return

    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await capture("end")
        await browser.close()

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--users', type=int, default=1)
    args = parser.parse_args()
    
    users = [{'id': i, 'email': f'vnirmal2722000@gmail.com', 'password': 'velu2000'} for i in range(args.users)]
    
    timestamp_dir = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    tasks = [
        user_flow(u, timestamp_dir, headless=False)
        for u in users
    ]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
