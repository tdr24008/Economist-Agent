"""CLI interface for Hybrid RAG Agent."""

import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.markdown import Markdown
from typing import Optional

from agent import hybrid_rag_agent, run_hybrid_rag_sync
from dependencies import SearchDependencies
from settings import load_settings

console = Console()

def show_banner():
    """Display the application banner."""
    banner = """
# Hybrid RAG Agent

Intelligent research assistant with:
- **Vector Search**: Semantic similarity matching
- **Hybrid Search**: Combined semantic + keyword search  
- **Graph Search**: Entity relationships and facts
- **Comprehensive Search**: Multi-method parallel search

Type your questions or use these commands:
- `help` - Show available commands
- `docs` - List available documents  
- `quit` - Exit the application
    """
    console.print(Panel(Markdown(banner), title="🔍 Welcome", border_style="blue"))

def show_help():
    """Display help information."""
    help_text = """
## Available Commands

- **General queries**: Ask any question to get comprehensive search results
- `docs` - List all available documents in the knowledge base
- `doc [id]` - Get details for a specific document by ID
- `help` - Show this help message
- `quit` / `exit` - Exit the application

## Example Queries

- "What is machine learning?"
- "How are neural networks related to AI?"
- "Find documents about natural language processing"
- "What are the relationships between transformers and NLP?"

The agent will automatically choose the best search method(s) for your query.
    """
    console.print(Panel(Markdown(help_text), title="📖 Help", border_style="green"))

async def handle_command(command: str, deps: SearchDependencies) -> Optional[str]:
    """Handle special commands."""
    command = command.strip().lower()
    
    if command in ['help', 'h']:
        show_help()
        return None
    
    elif command in ['docs', 'documents']:
        from agent import list_documents
        from pydantic_ai import RunContext
        ctx = RunContext(deps=deps, retry=0)
        return await list_documents(ctx, limit=20)
    
    elif command.startswith('doc '):
        doc_id = command[4:].strip()
        if doc_id:
            from agent import get_document
            from pydantic_ai import RunContext
            ctx = RunContext(deps=deps, retry=0)
            return await get_document(ctx, doc_id)
        else:
            return "Please provide a document ID. Example: doc doc-ai-fundamentals"
    
    elif command in ['quit', 'exit', 'q']:
        console.print("👋 Goodbye!", style="bold blue")
        return "QUIT"
    
    return None

async def run_cli():
    """Main CLI application loop."""
    show_banner()
    
    # Create properly initialized dependencies
    from dependencies import create_search_dependencies
    deps = await create_search_dependencies()
    
    if deps.use_mocks:
        console.print("🔧 Running in MOCK MODE - using sample data", style="yellow")
    
    while True:
        try:
            # Get user input
            query = Prompt.ask("\n[bold blue]Your question[/bold blue]", default="").strip()
            
            if not query:
                continue
            
            # Handle special commands
            command_result = await handle_command(query, deps)
            if command_result == "QUIT":
                break
            elif command_result is not None:
                console.print(Panel(command_result, title="📄 Results", border_style="cyan"))
                continue
            
            # Process regular queries with the agent
            console.print("🔍 Searching...", style="dim")
            
            try:
                result = await hybrid_rag_agent.run(query, deps=deps)
                
                # Display the result
                console.print(Panel(
                    Markdown(result.data), 
                    title="🎯 Answer", 
                    border_style="green"
                ))
                
                # Show tool calls if available
                if hasattr(result, 'all_messages') and result.all_messages:
                    tool_calls = [msg for msg in result.all_messages if hasattr(msg, 'tool_calls') and msg.tool_calls]
                    if tool_calls:
                        tools_used = []
                        for msg in tool_calls:
                            for tool_call in msg.tool_calls:
                                tools_used.append(tool_call.tool_name)
                        if tools_used:
                            console.print(f"🛠️  Tools used: {', '.join(set(tools_used))}", style="dim")
            
            except Exception as e:
                console.print(f"❌ Error: {str(e)}", style="bold red")
                console.print("Please try rephrasing your question.", style="dim")
        
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!", style="bold blue")
            break
        except EOFError:
            console.print("\n👋 Goodbye!", style="bold blue")
            break
    
    # Cleanup dependencies
    await deps.close()

def main():
    """Entry point for the CLI application."""
    try:
        asyncio.run(run_cli())
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="bold blue")

if __name__ == "__main__":
    main()