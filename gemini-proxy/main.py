from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
import requests
import google.auth
from google.auth.transport.requests import Request as GoogleAuthRequest
import json
import logging
import uuid
import re

app = FastAPI()
logging.basicConfig(level=logging.INFO)

# === Config ===
PROJECT_ID = "gemini-aider-dev"
LOCATION = "us-central1"
MODEL = "gemini-1.5-pro-preview-0409"
VAI_ENDPOINT = f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT_ID}/locations/{LOCATION}/publishers/google/models/{MODEL}:streamGenerateContent"

# === Token ===
def get_access_token():
    credentials, _ = google.auth.default()
    credentials.refresh(GoogleAuthRequest())
    return credentials.token

# === Utils ===
def sanitize_content(content):
    pattern = re.compile(r"(#\s?\*SEARCH/REPLACE block\* Rules:)", re.IGNORECASE)
    split = pattern.split(content)
    return split[0].strip() if split else content.strip()

def convert_messages(openai_messages):
    contents = []
    for msg in openai_messages:
        role = msg.get("role")
        content = msg.get("content", "")
        if role in ("user", "assistant") and content:
            contents.append({
                "role": role,
                "parts": [{"text": sanitize_content(content)}]
            })
    return contents

# === Core Chat Endpoint ===
@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    openai_messages = body.get("messages", [])
    stream = body.get("stream", True)

    logging.info(f"[{uuid.uuid4()}] ↩️ New chat request: {openai_messages[-1]['content'][:60]}...")

    vertex_payload = {
        "contents": convert_messages(openai_messages),
        "generationConfig": {
            "temperature": 0.7,
            "topP": 1,
            "topK": 40,
            "maxOutputTokens": 2048
        }
    }

    access_token = get_access_token()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(VAI_ENDPOINT, headers=headers, json=vertex_payload, stream=True)

    if response.status_code != 200:
        logging.error(f"❌ Gemini error {response.status_code}: {response.text}")
        return JSONResponse(status_code=500, content={
            "error": {
                "message": f"Gemini API error {response.status_code}",
                "details": response.text
            }
        })

    # === STREAMING MODE ===
    def stream_response():
        buffer = ""
        for line in response.iter_lines():
            if not line:
                continue
            line_str = line.decode("utf-8")
            if line_str.startswith("data: "):
                buffer += line_str[6:]
            else:
                buffer += line_str

            try:
                parsed_list = json.loads(buffer.strip())
                buffer = ""

                for idx_outer, item in enumerate(parsed_list):
                    candidate = item.get("candidates", [])[0]
                    parts = candidate["content"]["parts"]
                    for idx_inner, part in enumerate(parts):
                        delta_text = part.get("text", "")
                        chunk = {
                            "id": "chatcmpl-gemini2.5",
                            "object": "chat.completion.chunk",
                            "choices": [{
                                "delta": {"role": "assistant", "content": delta_text},
                                "index": 0,
                                "finish_reason": None
                            }]
                        }
                        yield f"data: {json.dumps(chunk)}\n\n"

                # Final stop
                yield f"data: {json.dumps({'choices': [{'finish_reason': 'stop'}]})}\n\n"
                logging.info("✅ Gemini streamed response complete.")

            except json.JSONDecodeError:
                continue
            except Exception as e:
                logging.warning(f"🔴 Stream parse failed: {e}")
                buffer = ""
                continue

    # === NON-STREAMING MODE ===
    if not stream:
        raw_response = response.json()
        full_text = ""

        for item in raw_response:
            try:
                candidate = item["candidates"][0]
                parts = candidate["content"]["parts"]
                for part in parts:
                    full_text += part.get("text", "")
            except Exception as e:
                logging.warning(f"⚠️ Skipped chunk: {e}")

        usage = {
            "prompt_tokens": len(json.dumps(openai_messages).split()),
            "completion_tokens": len(full_text.split()),
            "total_tokens": len(json.dumps(openai_messages).split()) + len(full_text.split())
        }

        return JSONResponse(content={
            "id": "chatcmpl-gemini2.5",
            "object": "chat.completion",
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": full_text
                },
                "finish_reason": "stop"
            }],
            "usage": usage
        })

    return StreamingResponse(stream_response(), media_type="text/event-stream")

# === LEGACY COMPLETIONS ENDPOINT ===
@app.post("/v1/completions")
async def legacy_completions(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")
    stream = body.get("stream", True)

    return await chat_completions(Request(scope=request.scope, receive=request._receive, send=request._send))

# === /v1/models ===
@app.get("/v1/models")
def list_models():
    return {
        "object": "list",
        "data": [{
            "id": "gpt-4",
            "object": "model",
            "created": 1677610602,
            "owned_by": "openai",
            "permission": []
        }]
    }
