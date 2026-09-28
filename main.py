"""
HR Email Finder — CLI Entry Point
Usage:
  python main.py run --input input/companies_sample.csv
  python main.py run --companies "Google, Stripe, Airbnb"
  python main.py dashboard
  python main.py config show
  python main.py test --company Google
"""
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from utils.config_loader import load_config, save_config, get_active_roles, get_enabled_tools
from utils.logger import get_logger

console = Console()
logger = get_logger("cli")


def print_banner():
    console.print(Panel.fit(
        "[bold cyan]📧 HR Email Finder[/bold cyan]\n"
        "[dim]Automated contact discovery • Multi-tool waterfall • Free + paid tools[/dim]",
        border_style="bright_blue",
        padding=(1, 4),
    ))


@click.group()
def cli():
    """HR Email Finder — multi-tool contact discovery pipeline."""
    print_banner()


# ──────────────────────────────────────────
# run command
# ──────────────────────────────────────────
@cli.command()
@click.option("--input", "-i", "input_file", default="", help="Path to CSV file with companies")
@click.option("--companies", "-c", default="", help="Comma-separated company names")
@click.option("--config", "config_path", default="config.yaml", help="Path to config.yaml")
@click.option("--output", "-o", default="", help="Override output directory")
def run(input_file, companies, config_path, output):
    """Run the email discovery pipeline."""
    from pipeline import Pipeline

    config = load_config(config_path)

    if output:
        config.setdefault("output", {})["directory"] = output

    enabled = get_enabled_tools(config)
    roles = get_active_roles(config)

    if not enabled:
        console.print("[yellow]⚠  No tools enabled! Defaulting to free_tools.[/yellow]")
        config["tools"]["free_tools"]["enabled"] = True

    # Summary table
    table = Table(box=box.ROUNDED, border_style="dim", show_header=False, padding=(0, 2))
    table.add_column(style="dim")
    table.add_column(style="bright_white")
    table.add_row("Tools", ", ".join(enabled) or "free_tools")
    table.add_row("Roles", ", ".join(roles[:5]) + ("..." if len(roles) > 5 else ""))
    table.add_row("Max/company", str(config.get("search", {}).get("max_per_company", 5)))
    table.add_row("Verify emails", "✓" if config.get("pipeline", {}).get("verify_emails") else "✗")
    console.print(table)
    console.print()

    pipe = Pipeline(config)

    if companies:
        company_list = [
            {"company_name": c.strip(), "website": ""}
            for c in companies.split(",")
            if c.strip()
        ]
        contacts = pipe.run(company_list)
    elif input_file:
        contacts = pipe.run_from_csv(input_file)
    else:
        # Interactive mode
        console.print("[cyan]Enter company names (one per line, blank line to start):[/cyan]")
        lines = []
        while True:
            line = input()
            if not line.strip():
                break
            lines.append(line.strip())
        if not lines:
            console.print("[red]No companies provided. Exiting.[/red]")
            return
        company_list = [{"company_name": c, "website": ""} for c in lines]
        contacts = pipe.run(company_list)

    # Print results table
    if contacts:
        result_table = Table(
            title=f"[bold green]✓ {len(contacts)} Contact(s) Found[/bold green]",
            box=box.ROUNDED,
            border_style="green",
            header_style="bold",
        )
        result_table.add_column("Name", style="bright_white", max_width=25)
        result_table.add_column("Title", style="cyan", max_width=30)
        result_table.add_column("Company", style="blue", max_width=20)
        result_table.add_column("Email", style="green", max_width=35)
        result_table.add_column("Conf.", justify="center")
        result_table.add_column("Verified", justify="center")

        for c in contacts:
            conf = f"{c.confidence:.0%}"
            verified = "✓" if c.email_verified else "—"
            result_table.add_row(c.name, c.title, c.company, c.email or "—", conf, verified)

        console.print(result_table)
    else:
        console.print("[yellow]No contacts found.[/yellow]")


# ──────────────────────────────────────────
# dashboard command
# ──────────────────────────────────────────
@cli.command()
@click.option("--port", default=5000, help="Port to run the dashboard on")
def dashboard(port):
    """Launch the web dashboard (opens in browser)."""
    import threading, webbrowser, time

    console.print(f"[green]🚀 Starting dashboard at http://localhost:{port}[/green]")

    def open_browser():
        time.sleep(1.5)
        webbrowser.open(f"http://localhost:{port}")

    threading.Thread(target=open_browser, daemon=True).start()

    # Add dashboard dir to path
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "dashboard"))
    from app import socketio, app
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)


# ──────────────────────────────────────────
# config command
# ──────────────────────────────────────────
@cli.group()
def config():
    """View and modify configuration."""


@config.command("show")
def config_show():
    """Print the current configuration summary."""
    cfg = load_config()
    roles = get_active_roles(cfg)
    enabled = get_enabled_tools(cfg)

    table = Table(title="Configuration Summary", box=box.ROUNDED)
    table.add_column("Section", style="dim")
    table.add_column("Setting", style="bright_white")
    table.add_column("Value", style="cyan")

    for tool_name, tool_cfg in cfg.get("tools", {}).items():
        table.add_row(
            "Tools",
            tool_name,
            "[green]✓ Enabled[/green]" if tool_cfg.get("enabled") else "[red]✗ Disabled[/red]",
        )

    table.add_row("Roles", "Active roles", str(len(roles)))
    for r in roles[:5]:
        table.add_row("", "", f"• {r}")

    p = cfg.get("pipeline", {})
    table.add_row("Pipeline", "Max workers", str(p.get("max_workers", 3)))
    table.add_row("Pipeline", "Verify emails", "✓" if p.get("verify_emails") else "✗")
    table.add_row("Pipeline", "Min confidence", f"{p.get('min_confidence', 0.5):.0%}")

    console.print(table)


@config.command("set-key")
@click.argument("tool")
@click.argument("api_key")
def config_set_key(tool, api_key):
    """Set an API key for a tool. Example: main.py config set-key hunter_io YOUR_KEY"""
    cfg = load_config()
    if tool not in cfg.get("tools", {}):
        console.print(f"[red]Unknown tool: {tool}[/red]")
        console.print(f"Available: {', '.join(cfg.get('tools', {}).keys())}")
        return
    cfg["tools"][tool]["api_key"] = api_key
    cfg["tools"][tool]["enabled"] = True
    save_config(cfg)
    console.print(f"[green]✓ API key set for {tool} (and tool enabled)[/green]")


@config.command("enable")
@click.argument("tool")
def config_enable(tool):
    """Enable a tool. Example: main.py config enable hunter_io"""
    cfg = load_config()
    if tool not in cfg.get("tools", {}):
        console.print(f"[red]Unknown tool: {tool}[/red]")
        return
    cfg["tools"][tool]["enabled"] = True
    save_config(cfg)
    console.print(f"[green]✓ {tool} enabled[/green]")


@config.command("disable")
@click.argument("tool")
def config_disable(tool):
    """Disable a tool."""
    cfg = load_config()
    if tool in cfg.get("tools", {}):
        cfg["tools"][tool]["enabled"] = False
        save_config(cfg)
        console.print(f"[yellow]✗ {tool} disabled[/yellow]")


# ──────────────────────────────────────────
# test command
# ──────────────────────────────────────────
@cli.command()
@click.option("--company", "-c", default="Stripe", help="Company to test with")
def test(company):
    """Quick test run against a single company."""
    from pipeline import Pipeline
    config = load_config()
    config["search"]["max_per_company"] = 3
    pipe = Pipeline(config)
    contacts = pipe.run([{"company_name": company, "website": ""}])
    console.print(f"\n[bold]Test result for [cyan]{company}[/cyan]:[/bold]")
    if contacts:
        for c in contacts:
            console.print(f"  • {c.name} ({c.title}) — {c.email or 'no email'} [{c.confidence:.0%}]")
    else:
        console.print("  [yellow]No contacts found[/yellow]")


if __name__ == "__main__":
    cli()
