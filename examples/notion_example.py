"""Notion example with authentication."""
import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import DocumentationAgent
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


async def example_notion_filter_database():
    """
    Example: Document how to filter a database in Notion.

    This demonstrates:
    - Authentication with email/password
    - Navigating Notion's complex SPA
    - Handling database views
    - Filter UI interactions
    """
    print("\n" + "="*60)
    print("NOTION EXAMPLE: Filter a Database")
    print("="*60)

    # Get credentials from environment or prompt
    email = os.getenv("NOTION_EMAIL")
    password = os.getenv("NOTION_PASSWORD")

    if not email or not password:
        print("\n⚠️  NOTION_EMAIL and NOTION_PASSWORD not found in .env")
        print("Please set these environment variables or update this script")
        print("\nYou can also set them now:")

        email = input("Notion email: ").strip() if not email else email
        password = input("Notion password: ").strip() if not password else password

        if not email or not password:
            print("❌ Email and password required")
            return

    # Initialize agent
    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    # Document the task
    print("\n📝 Starting Notion task documentation...")
    print(f"   Email: {email[:3]}***@{email.split('@')[1] if '@' in email else '***'}")

    result = await agent.document_task(
        question="How do I filter a database in Notion?",
        app_url="https://www.notion.so",
        credentials={
            "email": email,
            "password": password
        },
        output_dir="./output/notion_filter_database",
        max_steps=30  # Notion may need more steps
    )

    # Show results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)
    print(f"✅ Success: {result['success']}")
    print(f"📸 Screenshots: {result.get('total_steps', 0)}")
    print(f"⏱️  Duration: {result.get('total_duration', 'N/A')}")
    print(f"📁 Output: {result.get('output_directory', 'N/A')}")

    if result.get('guides'):
        print("\n📚 Generated guides:")
        for format_type, path in result['guides'].items():
            print(f"   • {format_type.upper()}: {path}")

        print(f"\n💡 Open the guide:")
        print(f"   open {result['guides']['html']}")

    if not result['success']:
        print(f"\n❌ Error: {result.get('error', 'Unknown error')}")

    return result


async def example_notion_create_page():
    """Example: Document how to create a page in Notion."""
    print("\n" + "="*60)
    print("NOTION EXAMPLE: Create a Page")
    print("="*60)

    email = os.getenv("NOTION_EMAIL")
    password = os.getenv("NOTION_PASSWORD")

    if not email or not password:
        print("⚠️  NOTION_EMAIL and NOTION_PASSWORD not set")
        return

    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    result = await agent.document_task(
        question="How do I create a new page in Notion?",
        app_url="https://www.notion.so",
        credentials={
            "email": email,
            "password": password
        },
        output_dir="./output/notion_create_page",
        max_steps=20
    )

    print(f"\n✅ Success: {result['success']}")
    print(f"📸 Screenshots: {result.get('total_steps', 0)}")

    return result


async def example_notion_create_database():
    """Example: Document how to create a database in Notion."""
    print("\n" + "="*60)
    print("NOTION EXAMPLE: Create a Database")
    print("="*60)

    email = os.getenv("NOTION_EMAIL")
    password = os.getenv("NOTION_PASSWORD")

    if not email or not password:
        print("⚠️  NOTION_EMAIL and NOTION_PASSWORD not set")
        return

    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    result = await agent.document_task(
        question="How do I create a new database in Notion?",
        app_url="https://www.notion.so",
        credentials={
            "email": email,
            "password": password
        },
        output_dir="./output/notion_create_database",
        max_steps=25
    )

    print(f"\n✅ Success: {result['success']}")
    print(f"📸 Screenshots: {result.get('total_steps', 0)}")

    return result


async def example_notion_sort_database():
    """Example: Document how to sort a database in Notion."""
    print("\n" + "="*60)
    print("NOTION EXAMPLE: Sort a Database")
    print("="*60)

    email = os.getenv("NOTION_EMAIL")
    password = os.getenv("NOTION_PASSWORD")

    if not email or not password:
        print("⚠️  NOTION_EMAIL and NOTION_PASSWORD not set")
        return

    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    result = await agent.document_task(
        question="How do I sort a database by a property in Notion?",
        app_url="https://www.notion.so",
        credentials={
            "email": email,
            "password": password
        },
        output_dir="./output/notion_sort_database",
        max_steps=25
    )

    print(f"\n✅ Success: {result['success']}")
    print(f"📸 Screenshots: {result.get('total_steps', 0)}")

    return result


async def main():
    """Run Notion examples."""
    print("\n🤖 Agent B - Notion Task Documentation Examples")
    print("="*60)

    # Check for credentials
    if not os.getenv("NOTION_EMAIL") or not os.getenv("NOTION_PASSWORD"):
        print("\n⚠️  To run these examples, you need Notion credentials:")
        print("   1. Add to your .env file:")
        print("      NOTION_EMAIL=your-email@example.com")
        print("      NOTION_PASSWORD=your-password")
        print("\n   2. Or export as environment variables:")
        print("      export NOTION_EMAIL=your-email@example.com")
        print("      export NOTION_PASSWORD=your-password")
        print("\n")

    # Run examples (uncomment the ones you want to run)
    await example_notion_filter_database()
    # await example_notion_create_page()
    # await example_notion_create_database()
    # await example_notion_sort_database()

    print("\n\n✨ Notion examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
