"""
Verification script for PlannerAgent.
Run this script to see how the PlannerAgent constructs prompts and parses responses.
"""

import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from agritech_core.agents import PlannerAgent
from agritech_core.config import Settings
from agritech_core.llm import OfflineLLMClient
from agritech_core.schemas import ChatRequest


def main():
    print("=== Verifying PlannerAgent (Offline Mode) ===")

    # 1. Setup
    settings = Settings(llm_mode="offline")
    # We use OfflineLLMClient which has a hardcoded stub for JSON requests
    llm = OfflineLLMClient()
    agent = PlannerAgent(llm=llm, settings=settings)

    # 2. Define a test scenario
    history = "USER: I have a small farm in Kenya.\nASSISTANT: That's great! What do you grow?"
    message = "I just planted some maize today."
    request = ChatRequest(message=message, location="Kenya")

    print(f"\n[Scenario]")
    print(f"History: {history}")
    print(f"User Message: {message}")

    # 3. Run the agent
    print(f"\n[Running Agent...]")
    actions = agent.build_actions(request, history)

    # 4. Inspect Results
    print(f"\n[Result]")
    print(f"Generated {len(actions)} actions:")
    for i, action in enumerate(actions, 1):
        print(f"{i}. [{action.priority.upper()}] {action.title}: {action.detail}")

    if len(actions) > 0:
        print("\n✅ SUCCESS: Agent generated actions.")
    else:
        print("\n❌ FAILURE: Agent failed to generate actions.")


if __name__ == "__main__":
    main()
