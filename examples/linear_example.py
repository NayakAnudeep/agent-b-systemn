"""Linear.app example with authentication."""
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


async def example_linear_create_project():
    """
    Example: Document how to create a project in Linear.

    This demonstrates:
    - Authentication with email/password
    - Navigating a complex SPA
    - Handling modals and forms
    - Multi-step workflows
    """
    print("\n" + "="*60)
    print("LINEAR EXAMPLE: Create a Project")
    print("="*60)

    # Get credentials from environment or prompt
    email = os.getenv("LINEAR_EMAIL")
    password = os.getenv("LINEAR_PASSWORD")

    if not email or not password:
        print("\n⚠️  LINEAR_EMAIL and LINEAR_PASSWORD not found in .env")
        print("Please set these environment variables or update this script")
        print("\nYou can also set them now:")

        email = input("Linear email: ").strip() if not email else email
        password = input("Linear password: ").strip() if not password else password

        if not email or not password:
            print("❌ Email and password required")
            return

    # Initialize agent
    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    # Document the task
    print("\n📝 Starting Linear task documentation...")
    print(f"   Email: {email[:3]}***@{email.split('@')[1] if '@' in email else '***'}")

    result = await agent.document_task(
        question="How do I create a new project in Linear?",
        app_url="https://linear.app",
        credentials={
            "email": email,
            "password": password
        },
        output_dir="./output/linear_create_project",
        max_steps=30  # Linear may need more steps
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


async def example_linear_filter_issues():
    """Example: Document how to filter issues in Linear."""
    print("\n" + "="*60)
    print("LINEAR EXAMPLE: Filter Issues")
    print("="*60)

    email = os.getenv("LINEAR_EMAIL")
    password = os.getenv("LINEAR_PASSWORD")

    if not email or not password:
        print("⚠️  LINEAR_EMAIL and LINEAR_PASSWORD not set")
        return

    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    result = await agent.document_task(
        question="How do I filter issues by priority in Linear?",
        app_url="https://linear.app",
        credentials={
            "email": email,
            "password": password
        },
        output_dir="./output/linear_filter_issues",
        max_steps=25
    )

    print(f"\n✅ Success: {result['success']}")
    print(f"📸 Screenshots: {result.get('total_steps', 0)}")

    return result


async def example_linear_create_issue():
    """Example: Document how to create an issue in Linear."""
    print("\n" + "="*60)
    print("LINEAR EXAMPLE: Create an Issue")
    print("="*60)

    email = os.getenv("LINEAR_EMAIL")
    password = os.getenv("LINEAR_PASSWORD")

    if not email or not password:
        print("⚠️  LINEAR_EMAIL and LINEAR_PASSWORD not set")
        return

    agent = DocumentationAgent(
        llm_provider="claude",
        model="claude-sonnet-4-20250514"
    )

    result = await agent.document_task(
        question="How do I create a new issue in Linear?",
        app_url="https://linear.app",
        credentials={
            "email": email,
            "password": password
        },
        output_dir="./output/linear_create_issue",
        max_steps=20
    )

    print(f"\n✅ Success: {result['success']}")
    print(f"📸 Screenshots: {result.get('total_steps', 0)}")

    return result


async def main():
    """Run Linear examples."""
    print("\n🤖 Agent B - Linear Task Documentation Examples")
    print("="*60)

    # Check for credentials
    if not os.getenv("LINEAR_EMAIL") or not os.getenv("LINEAR_PASSWORD"):
        print("\n⚠️  To run these examples, you need Linear credentials:")
        print("   1. Add to your .env file:")
        print("      LINEAR_EMAIL=your-email@example.com")
        print("      LINEAR_PASSWORD=your-password")
        print("\n   2. Or export as environment variables:")
        print("      export LINEAR_EMAIL=your-email@example.com")
        print("      export LINEAR_PASSWORD=your-password")
        print("\n")

    # Run examples (uncomment the ones you want to run)
    await example_linear_create_project()
    # await example_linear_filter_issues()
    # await example_linear_create_issue()

    print("\n\n✨ Linear examples completed!")


if __name__ == "__main__":
    asyncio.run(main())
