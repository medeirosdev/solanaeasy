"""
SolanaEasy CLI — Gerencie pagamentos Solana pelo terminal.

Uso:
    solanaeasy status <session_id>
    solanaeasy payments [--status CONFIRMED] [--limit 10]
    solanaeasy wait <session_id> [--timeout 120]
    solanaeasy --help
"""

from __future__ import annotations

import os
import sys

import click

from solanaeasy import SolanaEasy
from solanaeasy.exceptions import SolanaEasyError, SessionNotFoundError, WaitTimeout


# ── Helpers visuais ───────────────────────────────────────────────────────────

STATE_ICONS = {
    "CONFIRMED": "✅",
    "PENDING": "⏳",
    "FAILED": "❌",
    "EXPIRED": "⌛",
    "CREATED": "🆕",
}


def _icon(state: str) -> str:
    return STATE_ICONS.get(state, "❓")


def _make_sdk() -> SolanaEasy:
    """Cria instância do SDK a partir das variáveis de ambiente."""
    api_key = os.getenv("SOLANAEASY_API_KEY")
    if not api_key:
        click.echo(
            click.style("❌ SOLANAEASY_API_KEY não definida.", fg="red"),
            err=True,
        )
        click.echo("   Defina: export SOLANAEASY_API_KEY=sk_test_...", err=True)
        sys.exit(1)
    return SolanaEasy(api_key=api_key)


# ── Grupo principal ───────────────────────────────────────────────────────────


@click.group()
@click.version_option("0.1.0", prog_name="solanaeasy")
def cli() -> None:
    """SolanaEasy CLI — gerencie pagamentos Solana pelo terminal."""


# ── Comando: status ───────────────────────────────────────────────────────────


@cli.command()
@click.argument("session_id")
def status(session_id: str) -> None:
    """Verifica o status de uma sessão de pagamento.

    Exemplo:\n
        solanaeasy status sess_abc123
    """
    sdk = _make_sdk()
    try:
        s = sdk.check_status(session_id)
    except SessionNotFoundError:
        click.echo(click.style(f"❌ Sessão '{session_id}' não encontrada.", fg="red"))
        sys.exit(1)
    except SolanaEasyError as e:
        click.echo(click.style(f"❌ Erro: {e.message}", fg="red"))
        sys.exit(1)

    icon = _icon(s.state)
    state_color = "green" if s.state == "CONFIRMED" else "red" if s.state in ("FAILED", "EXPIRED") else "yellow"

    click.echo(f"\n{icon}  {click.style(s.state, fg=state_color, bold=True)} — {s.human_message}")
    click.echo(f"   {'Sessão:':10} {s.session_id}")

    if s.tx_hash:
        click.echo(f"   {'TX Hash:':10} {s.tx_hash}")
    if s.confirmed_at:
        click.echo(f"   {'Confirmado:':10} {s.confirmed_at.strftime('%d/%m/%Y %H:%M:%S UTC')}")
    if s.confirmation_time_ms:
        click.echo(f"   {'Tempo:':10} {s.confirmation_time_ms}ms")
    if s.error_code:
        click.echo(f"   {'Erro:':10} {click.style(s.error_code, fg='red')}")
    click.echo()


# ── Comando: payments ─────────────────────────────────────────────────────────


@cli.command()
@click.option("--status", "status_filter", default=None,
              type=click.Choice(["CREATED", "PENDING", "CONFIRMED", "FAILED", "EXPIRED"],
                                case_sensitive=False),
              help="Filtrar por estado.")
@click.option("--limit", default=10, show_default=True, help="Número de resultados.")
@click.option("--offset", default=0, show_default=True, help="Paginação.")
def payments(status_filter: str | None, limit: int, offset: int) -> None:
    """Lista pagamentos recentes do lojista.

    Exemplos:\n
        solanaeasy payments\n
        solanaeasy payments --status CONFIRMED\n
        solanaeasy payments --limit 20
    """
    sdk = _make_sdk()
    try:
        items = sdk.list_payments(status=status_filter, limit=limit, offset=offset)
    except SolanaEasyError as e:
        click.echo(click.style(f"❌ Erro: {e.message}", fg="red"))
        sys.exit(1)

    if not items:
        click.echo("Nenhum pagamento encontrado.")
        return

    click.echo(f"\n{'Estado':<12} {'Valor':>10}  {'Pedido':<20}  {'Sessão'}")
    click.echo("─" * 70)

    for p in items:
        icon = _icon(p.state)
        state_color = "green" if p.state == "CONFIRMED" else "red" if p.state in ("FAILED", "EXPIRED") else "yellow"
        state_str = click.style(f"{icon} {p.state:<10}", fg=state_color)
        amount_str = f"{p.amount:>8.2f} {p.currency}"
        click.echo(f"{state_str}  {amount_str}  {p.order_id:<20}  {p.session_id}")

    click.echo()


# ── Comando: wait ─────────────────────────────────────────────────────────────


@cli.command()
@click.argument("session_id")
@click.option("--timeout", default=120, show_default=True,
              help="Segundos máximos de espera.")
@click.option("--interval", default=2.0, show_default=True,
              help="Intervalo entre verificações em segundos.")
def wait(session_id: str, timeout: int, interval: float) -> None:
    """Aguarda a confirmação de um pagamento em tempo real.

    Exibe o estado atual a cada verificação até confirmar, falhar ou expirar.

    Exemplo:\n
        solanaeasy wait sess_abc123\n
        solanaeasy wait sess_abc123 --timeout 60
    """
    sdk = _make_sdk()

    def on_update(s: object) -> None:  # type: ignore[override]
        from solanaeasy.models import PaymentStatus
        if isinstance(s, PaymentStatus):
            icon = _icon(s.state)
            click.echo(f"  {icon}  {s.state} — {s.human_message}")

    click.echo(f"\n⏳ Aguardando confirmação de {session_id}...")
    click.echo(f"   Timeout: {timeout}s | Intervalo: {interval}s\n")

    try:
        final = sdk.wait_for_confirmation(
            session_id,
            timeout=timeout,
            poll_interval=interval,
            on_update=on_update,
        )
        icon = _icon(final.state)
        color = "green" if final.state == "CONFIRMED" else "red"
        click.echo(f"\n{icon}  {click.style(final.state, fg=color, bold=True)} — {final.human_message}")
        if final.tx_hash:
            click.echo(f"   TX: {final.tx_hash}")

    except WaitTimeout as e:
        click.echo(
            click.style(
                f"\n⌛ Timeout de {e.timeout}s atingido. Último estado: {e.last_status.state}",
                fg="yellow",
            )
        )
        sys.exit(1)
    except SolanaEasyError as e:
        click.echo(click.style(f"❌ Erro: {e.message}", fg="red"))
        sys.exit(1)

    click.echo()


if __name__ == "__main__":
    cli()
