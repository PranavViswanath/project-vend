"""Project Lend Orchestrator -- Claude Agent SDK multi-agent coordinator.

Manages the food bank donation system by coordinating:
- Inventory management (donation tracking and matching)
- Robot arm operations (sorting pipeline)
- Shelter email outreach (via Fetch.ai uAgent + MCP bridge)

Usage:
    python -m lend.agents.orchestrator
    python -m lend.agents.orchestrator --prompt "What shelters need fruit?"
"""

import asyncio
import os

from claude_agent_sdk import query, ClaudeAgentOptions, AgentDefinition


# Subagent definitions
AGENTS = {
    "inventory-manager": AgentDefinition(
        description=(
            "Manages food bank donation inventory. Use this agent to check "
            "current stock levels, analyze donation patterns, match donations "
            "to shelter needs, and generate inventory reports."
        ),
        prompt=(
            "You are the inventory manager for Project Lend, an autonomous food bank.\n\n"
            "Your responsibilities:\n"
            "- Track donation inventory by reading donations.json\n"
            "- Analyze donation patterns (categories, weights, timestamps)\n"
            "- Match current inventory against shelter demand\n"
            "- Recommend which donations should go to which shelters\n"
            "- Generate inventory summaries and reports\n\n"
            "The donation categories are: fruit, snack, drink.\n"
            "Each donation record has: id, category, item_name, estimated_weight_lbs, "
            "estimated_expiry, timestamp, image_path.\n\n"
            "Use the MCP tools (mcp__email-outreach__get_donation_inventory, "
            "mcp__email-outreach__get_shelter_needs, "
            "mcp__email-outreach__match_supply_to_demand) to access data.\n"
            "You can also read donations.json directly for detailed records."
        ),
        tools=["Read", "Grep", "Glob", "Bash"],
        model="haiku",
    ),
    "robot-operator": AgentDefinition(
        description=(
            "Controls the xArm 1S robotic sorting arm. Use this agent to "
            "start/stop the sorting pipeline, run calibration, test arm "
            "movements, or check robot status."
        ),
        prompt=(
            "You are the robot operator for Project Lend's sorting system.\n\n"
            "You control a Hiwonder xArm 1S robotic arm that sorts donated items into bins.\n\n"
            "Available commands:\n"
            "- python main.py --camera 1          # Run full auto pipeline (motion detection + sorting)\n"
            "- python main.py --camera 1 --no-arm # Vision-only mode (no arm movement)\n"
            "- python test_pipeline.py --camera 1  # Manual test mode (press SPACE to capture)\n"
            "- python test_arm.py                  # Test arm movements only\n"
            "- python calibrate.py                 # Calibrate arm positions\n\n"
            "The sorting categories: fruit -> BIN_FRUIT, snack -> BIN_SNACK, drink -> BIN_DRINK.\n\n"
            "IMPORTANT: Always warn the user before moving the robot arm. "
            "Never run arm commands without confirmation.\n"
            "Check if the arm is USB-connected before attempting operations."
        ),
        tools=["Bash", "Read"],
        model="haiku",
    ),
}

# MCP server config for the Fetch.ai bridge
MCP_SERVERS = {
    "email-outreach": {
        "command": sys.executable,
        "args": [
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "mcp_bridge.py"
            )
        ],
    }
}

# System prompt for the orchestrator
SYSTEM_PROMPT = """\
You are the orchestrator for Project Lend, an autonomous food bank donation system.

You coordinate multiple agents and tools:

1. **Inventory Manager** (subagent) -- tracks donations, analyzes patterns, matches supply to demand
2. **Robot Operator** (subagent) -- controls the sorting arm, runs the detection pipeline
3. **Email Outreach** (MCP tools) -- manages shelter registry, sends outreach emails, tracks demand

MCP tools available (prefix: mcp__email-outreach__):
- get_shelter_needs: get aggregated demand from all shelters
- get_shelter_registry: list all registered shelters
- get_active_shelters: list active shelters only
- add_shelter: register a new shelter
- update_shelter_needs: update what a shelter needs
- send_shelter_outreach: email a shelter asking what they need
- get_donation_inventory: current donation stats
- match_supply_to_demand: compare inventory vs shelter demand

When a user asks something:
- For inventory questions -> use inventory-manager subagent or MCP tools directly
- For robot/sorting questions -> use robot-operator subagent
- For shelter/email questions -> use MCP email-outreach tools
- For matching/distribution -> combine inventory + shelter data

Be concise and action-oriented. Suggest next steps proactively."""


async def run_orchestrator(prompt: str) -> str | None:
    """Run a single orchestrator query and return the result."""
    options = ClaudeAgentOptions(
        allowed_tools=[
            "Read",
            "Bash",
            "Grep",
            "Glob",
            "Task",
            "mcp__email-outreach__*",
        ],
        agents=AGENTS,
        mcp_servers=MCP_SERVERS,
        permission_mode="acceptEdits",
        system_prompt=SYSTEM_PROMPT,
    )

    result = None
    async for message in query(prompt=prompt, options=options):
        if hasattr(message, "result"):
            print(message.result)
            result = message.result
    return result


async def interactive_mode():
    """Run the orchestrator in interactive REPL mode."""
    print("=" * 60)
    print("  Project Lend Orchestrator")
    print("  Type your commands or 'quit' to exit")
    print("=" * 60)

    session_id = None

    while True:
        try:
            user_input = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nShutting down orchestrator.")
            break

        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print("Shutting down orchestrator.")
            break

        options = ClaudeAgentOptions(
            allowed_tools=[
                "Read",
                "Bash",
                "Grep",
                "Glob",
                "Task",
                "mcp__email-outreach__*",
            ],
            agents=AGENTS,
            mcp_servers=MCP_SERVERS,
            permission_mode="acceptEdits",
            system_prompt=SYSTEM_PROMPT,
        )

        # Resume session if we have one (maintains context)
        if session_id:
            options.resume = session_id

        async for message in query(prompt=user_input, options=options):
            if hasattr(message, "session_id"):
                session_id = message.session_id
            if hasattr(message, "result"):
                print(f"\n{message.result}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Project Lend Orchestrator")
    parser.add_argument(
        "--prompt",
        type=str,
        help="Single prompt to run (non-interactive)",
    )
    args = parser.parse_args()

    if args.prompt:
        asyncio.run(run_orchestrator(args.prompt))
    else:
        asyncio.run(interactive_mode())
