import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from litellm import ModelResponse


class FileCache:
    """
    基于文件系统的 LLM 调用缓存层。

    - 以 `cache_index` 作为子目录名称，用来区分一批缓存。
    - key 基于 chat 所需参数生成稳定哈希，用作文件名。
    - value 是人类可读、机器可解析的 JSON：
        {
          "request": { ...chat 参数... },
          "response": { ...ModelResponse 序列化... },
          "cached_at": "ISO 时间字符串"
        }
    """

    def __init__(self, cache_dir: str = ".cache") -> None:
        self._root = Path(cache_dir)

    def _ensure_dir(self, cache_index: str) -> Path:
        path = self._root / cache_index
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _make_key(self, params: Dict[str, Any]) -> str:
        """将请求参数序列化为确定性字符串，取 SHA-256 前 16 位作为 key。"""
        serialized = json.dumps(
            params,
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        return digest[:16]

    def get(self, cache_index: str, params: Dict[str, Any]) -> Optional[ModelResponse]:
        """读取缓存。命中返回 ModelResponse，未命中或出错返回 None。"""
        cache_dir = self._ensure_dir(cache_index)
        key = self._make_key(params)
        file_path = cache_dir / f"{key}.json"

        if not file_path.exists():
            return None

        try:
            with file_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return None

        response_data = data.get("response")
        if response_data is None:
            return None

        try:
            return ModelResponse(**response_data)
        except Exception:
            return None

    def set(
        self,
        cache_index: str,
        params: Dict[str, Any],
        response: ModelResponse,
    ) -> None:
        """写入缓存，将请求参数与响应一并保存为 JSON。"""
        cache_dir = self._ensure_dir(cache_index)
        key = self._make_key(params)
        file_path = cache_dir / f"{key}.json"

        if hasattr(response, "model_dump"):
            response_payload: Any = response.model_dump()
        elif hasattr(response, "dict"):
            response_payload = response.dict()
        else:
            response_payload = response

        payload = {
            "request": params,
            "response": response_payload,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=True)
