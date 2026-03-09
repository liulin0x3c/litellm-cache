from typing import Any, Dict, List, Literal, Optional

from litellm import ModelResponse, completion

from litellm_cache.file_cache import FileCache

Role = Literal["system", "user", "assistant"]


class MultiProviderClient:
    """
    使用 LiteLLM 统一调用多家模型供应商。

    通过传入不同的 `model` 字符串（如 "openai/gpt-4o"、"anthropic/claude-3-5-sonnet-20241022" 等），
    即可在不改业务代码的情况下切换底层模型供应商。
    """

    def __init__(
        self,
        default_model: str = "openai/gpt-4o",
        cache_dir: str = ".cache",
    ) -> None:
        self.default_model = default_model
        self._cache_dir = cache_dir
        self._file_cache: Optional[FileCache] = None

    def _get_cache(self) -> FileCache:
        if self._file_cache is None:
            self._file_cache = FileCache(self._cache_dir)
        return self._file_cache

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: Optional[str] = None,
        stream: bool = False,
        use_debug_cache: bool = False,
        cache_index: str = "default",
        **kwargs: Any,
    ) -> ModelResponse:
        """
        发送对话请求到指定模型，可选启用文件系统缓存。

        参数：
            messages:        对话消息列表
            model:           模型标识，如 "openai/gpt-4o"
            stream:          是否流式输出
            use_debug_cache: 是否启用文件缓存（仅非流式时生效）
            cache_index:     区分一批缓存的关键词，用作子目录名
        """
        selected_model = model or self.default_model

        cache_params: Dict[str, Any] = {
            "model": selected_model,
            "messages": messages,
            "stream": stream,
            "kwargs": kwargs,
        }

        if use_debug_cache and not stream:
            cache = self._get_cache()
            cached = cache.get(cache_index=cache_index, params=cache_params)
            if cached is not None:
                return cached

        response: ModelResponse = completion(
            model=selected_model,
            messages=messages,
            stream=stream,
            **kwargs,
        )

        if use_debug_cache and not stream:
            cache = self._get_cache()
            cache.set(cache_index=cache_index, params=cache_params, response=response)

        return response


def build_message(role: Role, content: str) -> Dict[str, str]:
    """消息构造辅助函数。"""
    return {"role": role, "content": content}
