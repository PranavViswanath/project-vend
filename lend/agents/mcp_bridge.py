"""MCP stdio server bridging Claude Agent SDK to the shelter registry.

Exposes tools for shelter management, donation inventory,
and supply/demand matching over the Model Context Protocol.
"""

import json
import os
import smtplib
from email.mime.text import MIMEText

from mcp.server.fastmcp import FastMCP
from lend.agents import shelter_registry
from lend.data import donations

mcp = FastMCP("project-lend-bridge")


def _send_email(to_addr, subject, body):
    """Send an email via SMTP. Raises if SMTP env vars are not configured."""
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")
    from_addr = os.environ.get("SMTP_FROM", smtp_user)

    if not all([smtp_host, smtp_user, smtp_pass]):
        raise RuntimeError(
            "SMTP not configured. Set SMTP_HOST, SMTP_USER, and SMTP_PASS environment variables."
        )

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr

    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def send_shelter_outreach(shelter_id: int, custom_message: str = "") -> str:
    """Send an outreach email to a shelter asking what food categories they need."""
    shelter = shelter_registry.get_shelter(shelter_id)
    if shelter is None:
        return json.dumps({"error": f"Shelter with id {shelter_id} not found"})

    name = shelter.get("name", "Shelter")
    email = shelter.get("email")
    if not email:
        return json.dumps({"error": f"Shelter '{name}' has no email address on file"})

    subject = f"Project Lend - What does {name} need this week?"
    body = (
        f"Hi {name},\n\n"
        "We have new donations coming in and want to make sure we send you "
        "the items you need most.\n\n"
        "Could you reply with the food categories you're currently looking for? "
        "(e.g. fruit, snacks, drinks)\n"
    )
    if custom_message:
        body += f"\n{custom_message}\n"
    body += "\nThank you,\nProject Lend Team"

    try:
        _send_email(email, subject, body)
        return json.dumps({"status": "sent", "to": email, "shelter": name})
    except RuntimeError as exc:
        return json.dumps({"error": str(exc)})
    except Exception as exc:
        return json.dumps({"error": f"Failed to send email: {exc}"})


@mcp.tool()
def get_shelter_needs() -> str:
    """Get aggregated demand summary from all active shelters."""
    try:
        summary = shelter_registry.get_demand_summary()
        return json.dumps(summary)
    except Exception as exc:
        return json.dumps({"error": f"Failed to get demand summary: {exc}"})


@mcp.tool()
def add_shelter(name: str, email: str, categories_needed: list[str] = None) -> str:
    """Add a new shelter to the registry."""
    try:
        record = shelter_registry.add_shelter(
            name=name, email=email, categories_needed=categories_needed
        )
        return json.dumps(record)
    except Exception as exc:
        return json.dumps({"error": f"Failed to add shelter: {exc}"})


@mcp.tool()
def update_shelter_needs(shelter_id: int, categories_needed: list[str]) -> str:
    """Update what food categories a specific shelter needs."""
    shelter = shelter_registry.get_shelter(shelter_id)
    if shelter is None:
        return json.dumps({"error": f"Shelter with id {shelter_id} not found"})

    try:
        updated = shelter_registry.update_shelter_needs(shelter_id, categories_needed)
        return json.dumps(updated)
    except Exception as exc:
        return json.dumps({"error": f"Failed to update shelter needs: {exc}"})


@mcp.tool()
def get_shelter_registry() -> str:
    """Get list of all shelters in the registry."""
    try:
        shelters = shelter_registry.get_all_shelters()
        return json.dumps(shelters)
    except Exception as exc:
        return json.dumps({"error": f"Failed to get shelters: {exc}"})


@mcp.tool()
def get_active_shelters() -> str:
    """Get list of active shelters only."""
    try:
        shelters = shelter_registry.get_active_shelters()
        return json.dumps(shelters)
    except Exception as exc:
        return json.dumps({"error": f"Failed to get active shelters: {exc}"})


@mcp.tool()
def get_donation_inventory() -> str:
    """Get current donation inventory stats from the sorting system."""
    try:
        stats = donations.get_stats()
        return json.dumps(stats)
    except Exception as exc:
        return json.dumps({"error": f"Failed to get donation stats: {exc}"})


@mcp.tool()
def match_supply_to_demand() -> str:
    """Compare current donation inventory with shelter demand to find surplus/deficit."""
    try:
        supply = donations.get_stats()
        demand = shelter_registry.get_demand_summary()

        supply_by_cat = supply.get("by_category", {})
        # get_demand_summary() returns a flat dict like {"fruit": 3, "snack": 1}
        demand_by_cat = demand

        all_categories = set(list(supply_by_cat.keys()) + list(demand_by_cat.keys()))

        matches = {}
        for cat in sorted(all_categories):
            have = supply_by_cat.get(cat, 0)
            need = demand_by_cat.get(cat, 0)
            matches[cat] = {
                "supply": have,
                "demand": need,
                "surplus": max(0, have - need),
                "deficit": max(0, need - have),
            }

        result = {
            "total_supply": supply.get("total_items", 0),
            "total_demand": sum(demand_by_cat.values()),
            "by_category": matches,
        }
        return json.dumps(result)
    except Exception as exc:
        return json.dumps({"error": f"Failed to match supply to demand: {exc}"})


if __name__ == "__main__":
    mcp.run(transport="stdio")
