from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def append_query_params(path: str, **params: object) -> str:
    raw_path = str(path or "").strip() or "/"
    split = urlsplit(raw_path)
    query = dict(parse_qsl(split.query, keep_blank_values=True))

    for key, value in params.items():
        if value is None:
            continue
        text = str(value).strip()
        if not text:
            continue
        query[str(key)] = text

    return urlunsplit((split.scheme, split.netloc, split.path or "/", urlencode(query), split.fragment))


def path_variants(path: str) -> list[str]:
    raw_path = str(path or "").strip() or "/"
    split = urlsplit(raw_path)
    base_path = split.path or "/"
    query = split.query
    fragment = split.fragment

    variants = [base_path]
    if base_path.endswith("/"):
        variants.append(base_path[:-1] or "/")
    else:
        variants.append(base_path + "/")

    ordered: list[str] = []
    seen: set[str] = set()
    for variant in variants:
        candidate = urlunsplit((split.scheme, split.netloc, variant, query, fragment))
        if candidate in seen:
            continue
        seen.add(candidate)
        ordered.append(candidate)

    return ordered
