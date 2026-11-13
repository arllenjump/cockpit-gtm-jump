import logging

from app.main import OcultarRetornoDoLogin


def registro(caminho):
    return logging.LogRecord(
        "uvicorn.access", logging.INFO, "", 0, '%s - "%s %s HTTP/%s" %d', ("1.2.3.4:5", "GET", caminho, "1.1", 307), None
    )


def test_oculta_codigo_do_retorno_da_microsoft():
    r = registro("/api/auth/callback?code=SEGREDO&state=x")
    OcultarRetornoDoLogin().filter(r)
    assert "SEGREDO" not in r.getMessage()
    assert "/api/auth/callback?[oculto]" in r.getMessage()


def test_mantem_outros_caminhos():
    r = registro("/api/health")
    OcultarRetornoDoLogin().filter(r)
    assert "/api/health" in r.getMessage()
