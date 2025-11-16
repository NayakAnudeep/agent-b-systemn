"""Basic usage example of Agent B Documentation System."""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import DocumentationAgent


async def example_google_search():
    """Example: Document how to search on Google."""
    print("Example 1: Google Search Documentation")
    print("="*60)

    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    result = await agent.document_task(
        question="How do I search for 'Python programming' on Google?",
        app_url="https://www.google.com",
        output_dir="./output/google_search"
    )

    print(f"\n✅ Task completed: {result['success']}")
    print(f"📸 Screenshots captured: {result.get('total_steps', 0)}")
    print(f"⏱️  Duration: {result.get('total_duration', 'N/A')}")

    if result.get('guides'):
        print(f"\n📄 Generated guides:")
        print(f"   Markdown: {result['guides']['markdown']}")
        print(f"   HTML: {result['guides']['html']}")
        print(f"   JSON: {result['guides']['json']}")


async def example_github_navigation():
    """Example: Document how to navigate GitHub."""
    print("\n\nExample 2: GitHub Navigation Documentation")
    print("="*60)

    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    result = await agent.document_task(
        question="How do I navigate to the Python repository on GitHub?",
        app_url="https://github.com",
        output_dir="./output/github_navigation"
    )

    print(f"\n✅ Task completed: {result['success']}")
    print(f"📸 Screenshots captured: {result.get('total_steps', 0)}")
    print(f"⏱️  Duration: {result.get('total_duration', 'N/A')}")


async def example_wikipedia_search():
    """Example: Document how to search Wikipedia."""
    print("\n\nExample 3: Wikipedia Search Documentation")
    print("="*60)

    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    result = await agent.document_task(
        question="How do I search for 'Artificial Intelligence' on Wikipedia?",
        app_url="https://www.wikipedia.org",
        output_dir="./output/wikipedia_search"
    )

    print(f"\n✅ Task completed: {result['success']}")
    print(f"📸 Screenshots captured: {result.get('total_steps', 0)}")
    print(f"⏱️  Duration: {result.get('total_duration', 'N/A')}")


async def main():
    """Run all examples."""
    print("\n🤖 Agent B - Web Task Documentation System")
    print("="*60)
    print("Running example tasks...\n")

    # Run examples (comment out ones you don't want to run)
    await example_google_search()
    # await example_github_navigation()
    # await example_wikipedia_search()

    print("\n\n✨ All examples completed!")
    print("Check the ./output directory for generated guides.")


if __name__ == "__main__":
    asyncio.run(main())
