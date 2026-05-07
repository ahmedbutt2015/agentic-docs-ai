from typing import Any, Dict, List, Optional


def chat_completion(
    messages: List[Dict[str, str]],
    provider: str,
    model: str,
    temperature: float = 0.1,
    max_tokens: int = 1500,
) -> str:
    if provider == "huggingface":
        return _huggingface_chat(messages, model, temperature, max_tokens)
    if provider == "anthropic":
        return _anthropic_chat(messages, model, temperature, max_tokens)
    raise ValueError(f"Unsupported LLM_PROVIDER: {provider!r} (use 'huggingface' or 'anthropic')")


def _huggingface_chat(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    from huggingface_hub import InferenceClient

    from app.config import HF_API_TOKEN

    if not HF_API_TOKEN:
        raise RuntimeError("HF_API_TOKEN is not set; cannot call Hugging Face inference.")

    client = InferenceClient(token=HF_API_TOKEN)
    response = client.chat_completion(
        messages=messages,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content or ""


def _anthropic_chat(
    messages: List[Dict[str, str]],
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    import anthropic

    from app.config import ANTHROPIC_API_KEY

    if not ANTHROPIC_API_KEY:
        raise RuntimeError("ANTHROPIC_API_KEY is not set; cannot call Anthropic.")

    system_prompt: Optional[str] = None
    user_messages: List[Dict[str, Any]] = []
    for message in messages:
        if message["role"] == "system":
            system_prompt = message["content"]
        else:
            user_messages.append({"role": message["role"], "content": message["content"]})

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    kwargs: Dict[str, Any] = {
        "model": model,
        "messages": user_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    if system_prompt:
        kwargs["system"] = system_prompt

    response = client.messages.create(**kwargs)
    return "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
