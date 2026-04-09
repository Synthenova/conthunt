from typing import Tuple


def _parse_stream_id(value: str) -> Tuple[int, int]:
    ms, seq = value.split("-", 1)
    return int(ms), int(seq)


def stream_id_gt(left: str, right: str) -> bool:
    if not right:
        return True
    return _parse_stream_id(left) > _parse_stream_id(right)
