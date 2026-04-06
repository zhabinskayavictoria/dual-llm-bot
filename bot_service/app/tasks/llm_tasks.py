import asyncio

import httpx

from app.core.config import settings
from app.infra.celery_app import celery_app

@celery_app.task(name="llm_request", bind=True, max_retries=2)
def llm_request(self, tg_chat_id: int, prompt: str) -> str:
    """Вызывает OpenRouter LLM и отправляет ответ пользователю в Telegram"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(_process_llm_request(tg_chat_id, prompt))
            return result
        finally:
            loop.close()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5)
    
    
async def _process_llm_request(tg_chat_id: int, prompt: str) -> str:
    """Выполняет запрос к OpenRouter API и отправляет ответ через Telegram Bot API"""
    url = f"{settings.OPENROUTER_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "HTTP-Referer": settings.OPENROUTER_SITE_URL,
        "X-Title": settings.OPENROUTER_APP_NAME,
        "Content-Type": "application/json",
    }
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        raise RuntimeError(
            f"OpenRouter API error: {response.status_code} — {response.text}"
        )
    data = response.json()
    try:
        answer = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise RuntimeError(f"Unexpected response format: {data}") from exc
    tg_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=15.0) as client:
        await client.post(tg_url, json={"chat_id": tg_chat_id, "text": answer})
    return answer