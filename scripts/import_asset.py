#!/usr/bin/env python3
"""Baixa uma mídia pública HTTPS e salva apenas em pastas aprovadas.

Uso: ASSET_URL=... TARGET_PATH=... python3 scripts/import_asset.py
As credenciais e URLs temporárias nunca são armazenadas em commits.
"""
import hashlib
import ipaddress
import os
import pathlib
import re
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

MAX_BYTES = 15 * 1024 * 1024
ROOT = pathlib.Path.cwd().resolve()
ALLOWED_FOLDERS = ("posts/", "videos/", "brand/logos/")
ALLOWED_HOSTS = (
    "media.canva.com",
    "storage.googleapis.com",
    "images.unsplash.com",
    "res.cloudinary.com",
)

def fail(reason: str) -> None:
    raise SystemExit(f"Importação recusada: {reason}")

def check_url(value: str) -> None:
    url = urllib.parse.urlsplit(value)
    if url.scheme != "https" or not url.hostname or url.username or url.password:
        fail("a origem deve usar HTTPS sem credenciais na URL")
    if not any(url.hostname == h or url.hostname.endswith("." + h) for h in ALLOWED_HOSTS):
        fail("domínio de origem não está na lista permitida")
    if url.port not in (None, 443):
        fail("porta HTTPS não permitida")
    for addr_info in socket.getaddrinfo(url.hostname, 443, type=socket.SOCK_STREAM):
        addr = ipaddress.ip_address(addr_info[4][0])
        if not addr.is_global:
            fail("endereço de rede não público")

class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        check_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def run():
    source = os.environ.get("ASSET_URL", "").strip()
    rel = os.environ.get("TARGET_PATH", "").strip()
    expected = os.environ.get("EXPECTED_SHA256", "").strip().lower()
    if not source or not rel:
        fail("URL e destino são obrigatórios")
    if not any(rel.startswith(folder) for folder in ALLOWED_FOLDERS):
        fail("destino precisa estar em posts/, videos/ ou brand/logos/")
    if not re.fullmatch(r"[A-Za-z0-9_./-]+", rel) or ".." in pathlib.PurePosixPath(rel).parts:
        fail("caminho de destino inválido")
    dest = (ROOT / rel).resolve()
    if not dest.is_relative_to(ROOT):
        fail("destino fora do repositório")
    if dest.exists():
        fail("arquivo já existe; escolha um nome novo para preservar o histórico")
    ext = dest.suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg", ".webp", ".mp4"}:
        fail("tipo de arquivo não permitido")
    if expected and not re.fullmatch(r"[a-f0-9]{64}", expected):
        fail("SHA-256 inválido")

    check_url(source)
    opener = urllib.request.build_opener(SafeRedirectHandler())
    request = urllib.request.Request(source, headers={"User-Agent": "ImpulseMarketingImporter/1.0"})
    try:
        with opener.open(request, timeout=45) as response:
            limit = response.headers.get("Content-Length")
            if limit and int(limit) > MAX_BYTES:
                fail("arquivo excede 15 MB")
            data = response.read(MAX_BYTES + 1)
    except (urllib.error.URLError, ValueError, TimeoutError) as error:
        fail(f"não foi possível baixar a mídia: {type(error).__name__}")
    if not data or len(data) > MAX_BYTES:
        fail("arquivo vazio ou maior que 15 MB")
    signatures = {
        ".png": data.startswith(b"\x89PNG\r\n\x1a\n"),
        ".jpg": data.startswith(b"\xff\xd8\xff"),
        ".jpeg": data.startswith(b"\xff\xd8\xff"),
        ".webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP",
        ".mp4": len(data) > 12 and data[4:8] == b"ftyp",
    }
    if not signatures[ext]:
        fail("o conteúdo não corresponde à extensão informada")
    digest = hashlib.sha256(data).hexdigest()
    if expected and digest != expected:
        fail("SHA-256 diferente do arquivo esperado")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    print(f"Arquivo validado: {rel} ({len(data)} bytes, sha256={digest})")

if __name__ == "__main__":
    run()
