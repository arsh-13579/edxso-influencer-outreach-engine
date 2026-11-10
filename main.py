import sqlite3
from rich.console import Console
from src.database import init_db, upsert_influencer, update_messages, export_submission_datasets, DB_PATH
from src.discovery import YouTubeDiscovery
from src.filter_enrich import evaluate_and_enrich
from src.personalizer import PersonalizationEngine
from src.sender import OutreachSender

console = Console()

def run_pipeline():
    console.rule("[bold blue]EDXSO AI Engineer Intern – Automated Micro-Influencer Outreach System")
    init_db()

    # Check if we already have 50+ profiles cached in SQLite DB
    conn = sqlite3.connect(DB_PATH)
    existing_count = conn.execute("SELECT COUNT(*) FROM influencers").fetchone()[0]
    conn.close()

    if existing_count >= 50:
        console.print(f"\n[bold green]✔ Found {existing_count} discovered & enriched influencers cached in local database (`data/outreach_system.db`). Skipping redundant YouTube API calls![/bold green]")
    else:
        try:
            console.print("\n[bold yellow]Step 1: Discovering 50+ Real Creators via YouTube Data API v3...[/bold yellow]")
            discovery = YouTubeDiscovery()
            raw_profiles = discovery.discover_channels(target_count=55)
            console.print(f"[green]✔ Discovered {len(raw_profiles)} unique channels.[/green]")

            console.print("\n[bold yellow]Step 2 & 3: Filtering & Enriching Profiles (Bio + Website Email Scraping)...[/bold yellow]")
            passed_count = 0
            for raw in raw_profiles:
                enriched = evaluate_and_enrich(raw)
                upsert_influencer(enriched)
                if enriched["filter_status"] == "PASSED":
                    passed_count += 1
            console.print(f"[green]✔ Enriched {len(raw_profiles)} profiles. Shortlisted (PASSED): {passed_count} influencers.[/green]")
        except Exception as e:
            console.print(f"[bold red]⚠ Network/API Error during live discovery: {e}[/bold red]")
            console.print("[yellow]Please check your internet connection and try again.[/yellow]")
            return

    # Step 4: AI Personalization
    console.print("\n[bold yellow]Step 4: Generating AI Personalized Emails (60-90w) & IG DMs (15-30w)...[/bold yellow]")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    shortlist = conn.execute("SELECT * FROM influencers WHERE filter_status = 'PASSED'").fetchall()
    conn.close()

    console.print(f"[cyan]Processing {len(shortlist)} shortlisted micro-influencers...[/cyan]")

    personalizer = PersonalizationEngine()
    sender = OutreachSender()

    for row in shortlist:
        profile = dict(row)
        if not profile.get("email_pitch"):
            msgs = personalizer.generate_outreach(profile)
            update_messages(
                profile["channel_id"],
                msgs.get("email_subject", "Collab Idea"),
                msgs.get("email_pitch", ""),
                msgs.get("instagram_dm", "")
            )
            profile.update(msgs)

        # Step 5: Sending Layer
        delivery_status = sender.send_email_outreach(profile)
        console.print(f"  • [cyan]{profile['name']}[/cyan] ({profile['email']}) -> [bold]{delivery_status}[/bold]")

    # Step 6: Export CSVs
    export_submission_datasets()
    console.print("\n[bold green]✔ Pipeline Complete! Submission CSVs exported to /data directory.[/bold green]")

if __name__ == "__main__":
    run_pipeline()