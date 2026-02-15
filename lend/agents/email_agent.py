"""Fetch.ai uAgent for email outreach to food shelters.

Contacts shelters to learn what donation categories they need,
parses responses, and maintains an aggregated demand summary.
Uses the Chat Protocol for ASI:One compatibility.
"""

import json
import logging
import os
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import anthropic
from uagents import Agent, Context, Protocol, Model
from uagents_core.contrib.protocols.chat import (
    ChatMessage,
    ChatAcknowledgement,
    TextContent,
    EndSessionContent,
    chat_protocol_spec,
)

from lend.agents.shelter_registry import (
    get_shelter,
    get_all_shelters,
    get_active_shelters,
    get_demand_summary,
    update_shelter,
    update_shelter_needs,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("email-outreach")

# SMTP configuration from environment
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

# Claude client for parsing responses and chat
CLAUDE_MODEL = os.getenv("CLAUDE_VISION_MODEL", "claude-3-5-haiku-latest")
claude_client = None
api_key = os.getenv("ANTHROPIC_API_KEY")
if api_key:
    claude_client = anthropic.Anthropic(api_key=api_key)

# Agent setup
AGENT_SEED = os.getenv("FETCHAI_AGENT_SEED", "project-lend-email-outreach-dev-seed")

agent = Agent(
    name="email-outreach",
    port=8001,
    seed=AGENT_SEED,
    mailbox=True,
    publish_agent_details=True,
)

# Check if email is configured
_email_configured = all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD])
if not _email_configured:
    logger.warning(
        "SMTP env vars not fully set (SMTP_HOST, SMTP_USER, SMTP_PASSWORD). "
        "Email sending is disabled. Demand queries still work."
    )


# ---------------------------------------------------------------------------
# Message models
# ---------------------------------------------------------------------------

class OutreachRequest(Model):
    shelter_id: int
    custom_message: str = ""


class ShelterNeedUpdate(Model):
    shelter_id: int
    categories_needed: list[str]


class DemandQuery(Model):
    pass


class DemandResponse(Model):
    demand: dict


# ---------------------------------------------------------------------------
# Email helpers
# ---------------------------------------------------------------------------

EMAIL_TEMPLATE = """\
Hello {name},

We hope this message finds you well! We're reaching out from Project Lend,
an autonomous food bank donation system.

We'd love to learn what types of donations your shelter currently needs so
we can help direct items your way. Our system sorts donations into these
categories:

  - Fruit (fresh produce, packaged fruit)
  - Snack (chips, granola bars, packaged snacks)
  - Drink (water, juice, beverages)

Could you reply and let us know which categories you need most right now?

{custom_section}
Thank you for the work you do in our community!

Best regards,
The Project Lend Team
"""


def send_outreach_email(shelter_name, shelter_email, custom_message=""):
    """Send an outreach email to a shelter asking what they need."""
    if not _email_configured:
        logger.warning("Email not configured, skipping send to %s", shelter_email)
        return False

    custom_section = ""
    if custom_message:
        custom_section = f"Additional note: {custom_message}\n\n"

    body = EMAIL_TEMPLATE.format(name=shelter_name, custom_section=custom_section)

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = shelter_email
    msg["Subject"] = "Project Lend - What donations does your shelter need?"
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
        logger.info("Outreach email sent to %s (%s)", shelter_name, shelter_email)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", shelter_email, e)
        return False


def parse_email_response(email_body):
    """Use Claude to parse a shelter's reply and extract categories needed.

    Returns list of category strings like ["fruit", "drink"].
    """
    if not claude_client:
        logger.warning("Anthropic client not configured, cannot parse email")
        return []

    prompt = (
        "A food shelter replied to our email asking what donation categories they need. "
        "The valid categories are: fruit, snack, drink.\n\n"
        "Extract which categories they need from this reply. "
        "Return ONLY a JSON array of lowercase category strings, e.g. [\"fruit\", \"drink\"]. "
        "If unclear, return an empty array [].\n\n"
        f"Shelter reply:\n{email_body}"
    )

    try:
        message = claude_client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
        )
        text = message.content[0].text.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            text = text.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
        categories = json.loads(text)
        valid = ["fruit", "snack", "drink"]
        return [c for c in categories if c in valid]
    except Exception as e:
        logger.error("Failed to parse email response: %s", e)
        return []


# ---------------------------------------------------------------------------
# Agent handlers
# ---------------------------------------------------------------------------

@agent.on_event("startup")
async def on_startup(ctx: Context):
    ctx.logger.info("Email outreach agent started")
    ctx.logger.info("Agent address: %s", ctx.agent.address)
    ctx.logger.info("Email configured: %s", _email_configured)
    shelters = get_active_shelters()
    ctx.logger.info("Active shelters in registry: %d", len(shelters))


@agent.on_interval(period=86400.0)
async def daily_outreach(ctx: Context):
    """Send outreach to active shelters not contacted in 7+ days."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    shelters = get_active_shelters()
    contacted = 0

    for shelter in shelters:
        last = shelter.get("last_contacted")
        if last:
            try:
                last_dt = datetime.fromisoformat(last)
                if last_dt > cutoff:
                    continue
            except ValueError:
                pass

        success = send_outreach_email(shelter["name"], shelter["email"])
        if success:
            update_shelter(
                shelter["id"],
                last_contacted=datetime.now(timezone.utc).isoformat(),
            )
            contacted += 1

    ctx.logger.info("Daily outreach complete: contacted %d shelters", contacted)


@agent.on_message(OutreachRequest)
async def handle_outreach_request(ctx: Context, sender: str, msg: OutreachRequest):
    """Send outreach email to a specific shelter."""
    shelter = get_shelter(msg.shelter_id)
    if not shelter:
        ctx.logger.warning("Shelter %d not found", msg.shelter_id)
        return

    success = send_outreach_email(
        shelter["name"], shelter["email"], msg.custom_message
    )
    if success:
        update_shelter(
            shelter["id"],
            last_contacted=datetime.now(timezone.utc).isoformat(),
        )
        ctx.logger.info("Outreach sent to shelter %d", msg.shelter_id)


@agent.on_message(DemandQuery)
async def handle_demand_query(ctx: Context, sender: str, msg: DemandQuery):
    """Return current demand summary."""
    demand = get_demand_summary()
    await ctx.send(sender, DemandResponse(demand=demand))


@agent.on_message(ShelterNeedUpdate)
async def handle_need_update(ctx: Context, sender: str, msg: ShelterNeedUpdate):
    """Update a shelter's needed categories."""
    result = update_shelter_needs(msg.shelter_id, msg.categories_needed)
    if result:
        ctx.logger.info(
            "Updated shelter %d needs to %s", msg.shelter_id, msg.categories_needed
        )
    else:
        ctx.logger.warning("Shelter %d not found for update", msg.shelter_id)


# ---------------------------------------------------------------------------
# Chat Protocol for ASI:One
# ---------------------------------------------------------------------------

chat_proto = Protocol(name="chat", version=chat_protocol_spec.version)


@chat_proto.on_message(ChatMessage)
async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle natural language queries from ASI:One about shelter needs."""
    # Acknowledge receipt
    await ctx.send(sender, ChatAcknowledgement(acknowledged_id=msg.msg_id))

    # Extract text from the message
    user_text = ""
    for item in msg.content:
        if isinstance(item, TextContent):
            user_text = item.text
            break

    if not user_text:
        await ctx.send(
            sender,
            ChatMessage(
                msg_id=ctx.new_msg_id(),
                content=[TextContent(text="I didn't receive any text to process.")],
            ),
        )
        return

    # Build context about current shelter demand
    demand = get_demand_summary()
    shelters = get_active_shelters()
    shelter_info = []
    for s in shelters:
        needs = ", ".join(s.get("categories_needed", [])) or "unknown"
        shelter_info.append(f"- {s['name']}: needs {needs}")

    context = (
        f"Current demand summary (number of shelters needing each category):\n"
        f"{json.dumps(demand, indent=2)}\n\n"
        f"Active shelters:\n" + "\n".join(shelter_info) if shelter_info
        else "No active shelters registered yet."
    )

    # Use Claude to generate a helpful response
    if claude_client:
        try:
            prompt = (
                "You are an assistant for Project Lend, a food bank donation system. "
                "Answer the user's question using the shelter data below.\n\n"
                f"Shelter data:\n{context}\n\n"
                f"User question: {user_text}"
            )
            response = claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )
            reply_text = response.content[0].text.strip()
        except Exception as e:
            logger.error("Claude chat error: %s", e)
            reply_text = f"Here's the current demand summary: {json.dumps(demand)}"
    else:
        reply_text = (
            f"Current demand across {len(shelters)} active shelters: "
            f"{json.dumps(demand)}"
        )

    await ctx.send(
        sender,
        ChatMessage(
            msg_id=ctx.new_msg_id(),
            content=[TextContent(text=reply_text)],
        ),
    )


agent.include(chat_proto, publish_manifest=True)


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent.run()
