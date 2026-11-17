#!/usr/bin/env python3
"""Upload de uma arte local aprovada para o GitHub via Contents API.

Exige GITHUB_TOKEN com permissão contents:write restrita ao repositório.
Uso: python3 scripts/upload_from_file.py /caminho/arte.png posts/2026/11/arte.png
Não publica nem agenda redes sociais.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

REPO = "ivanramosdossantos/impulse-marketing-assets"
MAX_BYTES = 15 * 1024 * 1024
ALLOWED_PREFIXES = ("posts/", "videos/", "brand/logos/")
ALLOWED_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".mp4"}


def validate_target(path: str) -> str:
    if not path or not re.fullmatch(r"[A-Za-z0-9_./-]+", path):
        raise ValueError("Destino deve conter somente letras, números, /, _, -, e .")
    if not path.startswith(ALLOWED_PREFIXES) or ".." in PurePosixPath(path).parts:
        raise ValueError("Destino fora das pastas permitidas")
    if PurePosixPath(path).suffix.lower() not in ALLOWED_SUFFIXES:
        raise ValueError("Extensão de arquivo não permitida")
    return path


def validate_media(data: bytes, extension: str) -> None:
    if not data or len(data) > MAX_BYTES:
        raise ValueError("Arquivo vazio ou maior que 15 MB")
    signatures = {
        ".png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": data.startswith(b"\xff\xd8\xff"),
        ".jpeg": data.startswith(b"\xff\xd8\xff"),
        ".webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP",
        ".mp4": len(data) > 12 and data[4:8] == b"ftyp",
    }
    if not signatures.get(extension, False):
        raise ValueError("Conteúdo não corresponde à extensão")


def api_call(token: str, path: str, method: str, body: bytes | None = None):
    encoded_path = urllib.parse.quote(path, safe="/")
    url = f"https://api.github.com/repos/{REPO}/contents/{encoded_path}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "ImpulseMarketingUpload/1.0",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, headers=headers, data=body, method=method)
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return 404, None
        # GitHub errors may include sensitive details; don't echo tokens or payload.
        raise RuntimeError(f"GitHub HTTP {exc.code} em {method} {path}") from None


def upload(path: Path, target: str, token: str) -> dict:
    target = validate_target(target)
    if path.suffix.lower() != PurePosixPath(target).suffix.lower():
        raise ValueError("Extensões de origem e destino devem coincidir")
    data = path.read_bytes()
    validate_media(data, path.suffix.lower())
    status, _ = api_call(token, target, "GET")
    if status != 404:
        raise FileExistsError("O destino já existe. Não sobrescrever artes aprovadas.")
    payload = {
        "message": "assets: upload approved marketing image",
        "content": base64.b64encode(data).decode("ascii"),
        "branch": "main",
    }
    status, response = api_call(
        token, target, "PUT", json.dumps(payload).encode("utf-8")
    )
    if status != 201:
        raise RuntimeError(f"Upload não confirmado (HTTP {status})")
    return {
        "path": target,
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "commit_sha": response["commit"]["sha"],
        "github_url": response["content"]["html_url"],
        "public_url": "https://raw.githubusercontent.com/" + REPO + "/main/" + urllib.parse.quote(target, safe="/"),
    }


def main():
    if len(sys.argv) != 3:
        raise SystemExit("Uso: upload_from_file.py <imagem_local> <destino_repo>")
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        raise SystemExit("GITHUB_TOKEN não configurado; nenhuma chamada realizada")
    print(json.dumps(upload(Path(sys.argv[1]), sys.argv[2], token), ensure_ascii=False))


if __name__ == "__main__":
    main()
