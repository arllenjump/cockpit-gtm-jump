"""Adapter do ICP Jump (docs/03-integracoes.md).

Modo escolhido por ICP_JUMP_MODE:
- fixture: lê api/fixtures/icp-jump-contas.json (contas fictícias da simulação piloto).
- api: ICP Jump real. Rotas e autenticação ainda não confirmadas; não implementado.
"""
import json
from pathlib import Path

from app.config import env

FIXTURE = Path(__file__).resolve().parent.parent / "fixtures" / "icp-jump-contas.json"


def modo() -> str:
    return env("ICP_JUMP_MODE", "fixture")


def _contas() -> list[dict]:
    if modo() == "fixture":
        return json.loads(FIXTURE.read_text(encoding="utf-8"))["contas"]
    if modo() == "api":
        raise NotImplementedError("ICP_JUMP_MODE=api: rotas do ICP Jump ainda não confirmadas.")
    raise ValueError(f"ICP_JUMP_MODE inválido: {modo()!r} (use 'fixture' ou 'api').")


def list_accounts(min_score: int | None = None, vertical: str | None = None, has_active_signals: bool | None = None) -> list[dict]:
    """Contas ordenadas pelo GTM Score, do maior para o menor."""
    contas = _contas()
    if min_score is not None:
        contas = [c for c in contas if c["gtm_score"] >= min_score]
    if vertical is not None:
        contas = [c for c in contas if c["sector"] == vertical]
    if has_active_signals is not None:
        contas = [c for c in contas if bool(c["signals"]) == has_active_signals]
    return sorted(contas, key=lambda c: c["gtm_score"], reverse=True)


def get_account(external_id: str) -> dict | None:
    """Conta com dossiê e decisores, ou None se não existir."""
    return next((c for c in _contas() if c["external_id"] == external_id), None)
