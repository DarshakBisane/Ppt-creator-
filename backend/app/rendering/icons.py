"""Semantic Icon Abstraction Layer mapping presentation concepts to visual symbols and badges."""

from typing import Any

# High-fidelity semantic symbols and badge icons
CONCEPT_ICON_MAP: dict[str, str] = {
    # Security & Cryptography
    "certificate": "📜",
    "cert": "📜",
    "x509": "📜",
    "x.509": "📜",
    "pki": "🏛️",
    "ca": "🏛️",
    "authority": "🏛️",
    "root ca": "👑",
    "subordinate ca": "🏛️",
    "registration authority": "📋",
    "ra": "📋",
    "public key": "🔑",
    "private key": "🔒",
    "key": "🔑",
    "security": "🛡️",
    "secure": "🛡️",
    "shield": "🛡️",
    "lock": "🔒",
    "unlock": "🔓",
    "encryption": "🔐",
    "encrypt": "🔐",
    "decrypt": "🔓",
    "signature": "✍️",
    "digital signature": "✍️",
    "hash": "🔢",
    "integrity": "✨",
    "trust": "🤝",
    "trusted": "✅",
    "untrusted": "❌",
    "verification": "🔍",
    "verify": "🔍",
    "audit": "📋",
    "compliance": "⚖️",
    "policy": "📜",
    "ocsp": "⚡",
    "crl": "📑",
    "revocation": "🚫",
    "revoke": "🚫",
    "renewal": "🔄",
    "renew": "🔄",
    "expiration": "⏳",
    "expire": "⏳",
    "lifecycle": "♻️",
    "handshake": "🤝",
    "tls": "🔒",
    "ssl": "🔒",

    # Architecture & Infrastructure
    "user": "👤",
    "client": "💻",
    "browser": "🌐",
    "server": "🖥️",
    "database": "🗄️",
    "db": "🗄️",
    "storage": "💾",
    "cloud": "☁️",
    "api": "🔌",
    "endpoint": "📍",
    "gateway": "🚪",
    "network": "🌐",
    "cluster": "🧩",
    "container": "📦",
    "kubernetes": "☸️",
    "microservice": "⚙️",
    "service": "⚙️",
    "queue": "📬",
    "message": "✉️",
    "bus": "🚌",
    "cache": "⚡",
    "load balancer": "⚖️",
    "proxy": "🛡️",
    "firewall": "🧱",

    # Process & Workflow
    "step": "▶️",
    "phase": "📌",
    "workflow": "🔄",
    "process": "⚙️",
    "pipeline": "🚀",
    "deployment": "📦",
    "ci/cd": "🔄",
    "monitor": "📊",
    "analytics": "📈",
    "metrics": "📊",
    "kpi": "🎯",
    "target": "🎯",
    "growth": "📈",
    "speed": "⚡",
    "performance": "⚡",
    "latency": "⏱️",
    "throughput": "🏎️",
    "availability": "🟢",
    "uptime": "🟢",
    "alert": "⚠️",
    "warning": "⚠️",
    "error": "❌",
    "success": "✅",
    "document": "📄",
    "report": "📑",
    "summary": "📋",
    "strategy": "♟️",
    "vision": "🔭",
    "milestone": "🏁",
    "flag": "🚩",
    "calendar": "📅",
    "clock": "⏰",
    "idea": "💡",
    "innovation": "💡",
    "quantum": "⚛️",
    "algorithm": "🧮",
    "data": "📊",
}


def get_semantic_icon(text: str, default: str = "📌") -> str:
    """Extract the most relevant semantic icon symbol for a given title or concept text."""
    if not text:
        return default

    clean_text = text.lower().strip()

    # Exact match first
    if clean_text in CONCEPT_ICON_MAP:
        return CONCEPT_ICON_MAP[clean_text]

    # Keyword search (longest keyword match wins)
    best_match: str | None = None
    best_len = 0

    for keyword, icon in CONCEPT_ICON_MAP.items():
        if keyword in clean_text and len(keyword) > best_len:
            best_match = icon
            best_len = len(keyword)

    return best_match if best_match else default
