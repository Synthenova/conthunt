import asyncio
from typing import Dict, Optional, Set, Tuple

import redis.asyncio as redis


def _parse_stream_id(value: str) -> Tuple[int, int]:
    ms, seq = value.split("-", 1)
    return int(ms), int(seq)


def stream_id_gt(left: str, right: str) -> bool:
    if not right:
        return True
    return _parse_stream_id(left) > _parse_stream_id(right)


class StreamFanoutHub:
    def __init__(self, client: redis.Redis, logger):
        self._client = client
        self._logger = logger
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._last_ids: Dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._stop_event = asyncio.Event()
        self._task: Optional[asyncio.Task] = None
        self._read_failures: int = 0
        self._read_recoveries: int = 0

    async def start(self) -> None:
        if self._task:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._reader_loop())

    async def stop(self) -> None:
        if not self._task:
            return
        self._stop_event.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None

    async def subscribe(self, stream_key: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        async with self._lock:
            if stream_key not in self._subscribers:
                self._subscribers[stream_key] = set()
                self._last_ids[stream_key] = "$"
            self._subscribers[stream_key].add(queue)
        return queue

    async def unsubscribe(self, stream_key: str, queue: asyncio.Queue) -> None:
        async with self._lock:
            subscribers = self._subscribers.get(stream_key)
            if not subscribers:
                return
            subscribers.discard(queue)
            if not subscribers:
                self._subscribers.pop(stream_key, None)
                self._last_ids.pop(stream_key, None)

    async def _reader_loop(self) -> None:
        backoff_s = 0.5
        while not self._stop_event.is_set():
            async with self._lock:
                if not self._subscribers:
                    streams = None
                else:
                    streams = dict(self._last_ids)

            if not streams:
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=0.2)
                except asyncio.TimeoutError:
                    pass
                continue

            try:
                results = await self._client.xread(streams, count=100, block=10000)
            except Exception as exc:
                self._read_failures += 1
                self._logger.warning(
                    "Stream hub read failed: %s (failures=%s backoff=%.2fs)",
                    exc,
                    self._read_failures,
                    backoff_s,
                )
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=backoff_s)
                except asyncio.TimeoutError:
                    pass
                backoff_s = min(backoff_s * 2.0, 5.0)
                continue

            if self._read_failures > 0:
                self._read_recoveries += 1
                self._logger.info(
                    "Stream hub read recovered (recoveries=%s previous_failures=%s)",
                    self._read_recoveries,
                    self._read_failures,
                )
                self._read_failures = 0
            backoff_s = 0.5

            if not results:
                continue

            for stream_key, messages in results:
                for msg_id, data_map in messages:
                    payload = data_map.get("data")
                    async with self._lock:
                        self._last_ids[stream_key] = msg_id
                        subscribers = list(self._subscribers.get(stream_key, ()))

                    if not subscribers:
                        continue

                    item = (msg_id, payload)
                    for queue in subscribers:
                        try:
                            queue.put_nowait(item)
                        except asyncio.QueueFull:
                            try:
                                queue.get_nowait()
                            except asyncio.QueueEmpty:
                                pass
                            try:
                                queue.put_nowait(item)
                            except asyncio.QueueFull:
                                pass
