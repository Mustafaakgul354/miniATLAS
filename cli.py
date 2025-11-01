#!/usr/bin/env python3
"""Interactive CLI for mini-Atlas browser agent."""

import asyncio
import sys
from typing import Optional

import httpx
import rich
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

console = Console()


class MiniAtlasCLI:
    """Interactive CLI client for mini-Atlas."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def close(self):
        """Close the client."""
        await self.client.aclose()
    
    async def run_interactive(self):
        """Run interactive session creation."""
        console.print("\n[bold cyan]🤖 mini-Atlas Browser Agent[/bold cyan]\n")
        
        # Get URL
        url = Prompt.ask(
            "[bold]Başlangıç URL'i[/bold]",
            default="https://www.example.com",
            console=console
        )
        
        # Validate URL
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"
            console.print(f"[yellow]URL'ye https:// eklendi: {url}[/yellow]")
        
        # Get goals
        console.print("\n[bold]Hedeflerinizi belirtin (her hedef için Enter'a basın, bitirmek için boş bırakın):[/bold]")
        goals = []
        goal_num = 1
        
        while True:
            goal = Prompt.ask(
                f"  Hedef {goal_num}",
                default="" if goal_num == 1 else None,
                console=console
            )
            
            if not goal and goals:
                break
            
            if goal:
                goals.append(goal)
                goal_num += 1
            
            if not goals:
                console.print("[red]En az bir hedef belirtmelisiniz![/red]")
                continue
        
        # Optional profile
        use_profile = Confirm.ask(
            "\n[bold]Oturum için profil bilgisi eklemek istiyor musunuz?[/bold]",
            default=False,
            console=console
        )
        
        profile = None
        if use_profile:
            email = Prompt.ask("  Email", console=console)
            password = Prompt.ask("  Şifre", password=True, console=console)
            profile = {"email": email, "password": password}
        
        # Optional settings
        max_steps = Prompt.ask(
            "\n[bold]Maksimum adım sayısı[/bold]",
            default="20",
            console=console
        )
        
        # Confirm and start
        console.print("\n[bold]Özet:[/bold]")
        console.print(f"  URL: [cyan]{url}[/cyan]")
        console.print(f"  Hedefler: [cyan]{len(goals)} adet[/cyan]")
        for i, goal in enumerate(goals, 1):
            console.print(f"    {i}. {goal}")
        if profile:
            console.print(f"  Profil: [cyan]{profile['email']}[/cyan]")
        console.print(f"  Maksimum adım: [cyan]{max_steps}[/cyan]")
        
        if not Confirm.ask("\n[bold]Başlatmak istiyor musunuz?[/bold]", default=True, console=console):
            console.print("[yellow]İptal edildi.[/yellow]")
            return
        
        # Start session
        await self.start_session(url, goals, profile, int(max_steps))
    
    async def start_session(
        self,
        url: str,
        goals: list,
        profile: Optional[dict] = None,
        max_steps: int = 20
    ):
        """Start a new agent session and monitor it."""
        try:
            # Prepare request
            data = {
                "url": url,
                "goals": goals,
                "max_steps": max_steps,
                "session_mode": "ephemeral"
            }
            if profile:
                data["profile"] = profile
            
            # Start session
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Agent başlatılıyor...", total=None)
                
                response = await self.client.post(
                    f"{self.base_url}/run",
                    json=data
                )
                response.raise_for_status()
                result = response.json()
                
                session_id = result["session_id"]
                progress.update(task, description=f"Session başlatıldı: {session_id}")
            
            console.print(f"\n[green]✓ Session başlatıldı:[/green] [cyan]{session_id}[/cyan]")
            console.print(f"[dim]Durum izleniyor... (Ctrl+C ile durdurabilirsiniz)[/dim]\n")
            
            # Monitor session
            await self.monitor_session(session_id)
            
        except httpx.HTTPError as e:
            console.print(f"\n[red]✗ Hata:[/red] {e}")
            if hasattr(e, 'response') and e.response:
                console.print(f"[red]Detay:[/red] {e.response.text}")
        except KeyboardInterrupt:
            console.print("\n[yellow]İzleme durduruldu.[/yellow]")
        except Exception as e:
            console.print(f"\n[red]✗ Beklenmeyen hata:[/red] {e}")
    
    async def monitor_session(self, session_id: str, poll_interval: int = 2):
        """Monitor session progress."""
        last_step = -1
        
        try:
            while True:
                response = await self.client.get(f"{self.base_url}/status/{session_id}")
                response.raise_for_status()
                status = response.json()
                
                state = status["state"]
                current_step = status["steps_done"]
                current_url = status.get("current_url", "")
                
                # Show new step
                if current_step > last_step:
                    if status.get("last_action"):
                        action = status["last_action"]
                        action_type = action.get("action", "unknown")
                        selector = action.get("selector", "")
                        
                        console.print(
                            f"[cyan]Adım {current_step}:[/cyan] "
                            f"[bold]{action_type}[/bold]"
                            + (f" → {selector}" if selector else "")
                        )
                    
                    last_step = current_step
                
                # Check if done
                if state in ("completed", "failed", "stopped"):
                    console.print(f"\n[bold]Durum:[/bold] ", end="")
                    
                    if state == "completed":
                        console.print("[green]Tamamlandı ✓[/green]")
                    elif state == "failed":
                        console.print("[red]Başarısız ✗[/red]")
                        if status.get("error"):
                            console.print(f"[red]Hata:[/red] {status['error']}")
                    else:
                        console.print(f"[yellow]{state}[/yellow]")
                    
                    # Show final URL
                    if current_url:
                        console.print(f"[dim]Son URL: {current_url}[/dim]")
                    
                    break
                
                # Check for CAPTCHA
                if state == "waiting_human" or status.get("has_captcha"):
                    console.print("\n[bold yellow]⚠ CAPTCHA tespit edildi![/bold yellow]")
                    console.print("[yellow]CAPTCHA'yı manuel olarak çözün ve ardından devam edin.[/yellow]")
                    
                    if Confirm.ask("\n[bold]CAPTCHA çözüldü, devam edilsin mi?[/bold]", default=True, console=console):
                        await self.client.post(
                            f"{self.base_url}/agent/continue/{session_id}",
                            json={"note": "CAPTCHA manually solved"}
                        )
                        console.print("[green]Devam ediliyor...[/green]\n")
                    else:
                        break
                
                await asyncio.sleep(poll_interval)
                
        except KeyboardInterrupt:
            console.print("\n[yellow]İzleme durduruldu.[/yellow]")
            console.print(f"[dim]Session hala çalışıyor: {session_id}[/dim]")
        except Exception as e:
            console.print(f"\n[red]✗ İzleme hatası:[/red] {e}")


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="mini-Atlas Browser Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  # İnteraktif mod
  python cli.py
  
  # Direkt çalıştırma
  python cli.py --url "https://example.com" --goal "Login ol" --goal "Dashboard'a git"
        """
    )
    
    parser.add_argument(
        "--url",
        help="Başlangıç URL'i"
    )
    parser.add_argument(
        "--goal",
        action="append",
        dest="goals",
        help="Hedef (birden fazla eklenebilir)"
    )
    parser.add_argument(
        "--email",
        help="Profil email adresi"
    )
    parser.add_argument(
        "--password",
        help="Profil şifresi"
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=20,
        help="Maksimum adım sayısı (varsayılan: 20)"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="API base URL (varsayılan: http://localhost:8000)"
    )
    
    args = parser.parse_args()
    
    cli = MiniAtlasCLI(base_url=args.base_url)
    
    try:
        if args.url and args.goals:
            # Direct mode
            profile = None
            if args.email and args.password:
                profile = {"email": args.email, "password": args.password}
            
            await cli.start_session(
                url=args.url,
                goals=args.goals,
                profile=profile,
                max_steps=args.max_steps
            )
        else:
            # Interactive mode
            await cli.run_interactive()
    finally:
        await cli.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n[yellow]Çıkılıyor...[/yellow]")
        sys.exit(0)

