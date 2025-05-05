import argparse
from sage import SAGE
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box
from rich.live import Live
from rich.align import Align
import time
import random

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the SAGE protocol on a prompt.")
    parser.add_argument("--prompt", type=str, default=None, help="Prompt to process (if not provided, uses default test prompt)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    console = Console()

    # Green-cyan color for banner
    banner_color = "bold bright_cyan"

    # Welcome message panel
    welcome = Panel(
        "[bold green]*[/bold green] Welcome to the SAGE Protocol!",
        style="bold white on black",
        border_style="green"
    )
    console.print(welcome, justify="center")

    ascii_art = '''
███████╗ █████╗  ██████╗ ███████╗
██╔════╝██╔══██╗██╔════╝ ██╔════╝
███████╗███████║██║  ███╗█████╗  
╚════██║██╔══██║██║   ██║██╔══╝  
███████║██║  ██║╚██████╔╝███████╗
╚══════╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝
'''
    # Center and color the ASCII art in green
    for line in ascii_art.strip().splitlines():
        console.print(f"[bold green]{line.center(50)}[/bold green]", justify="center")

    # Animated loading dots
    with Live(Align.center("[green]Initializing", vertical="middle"), refresh_per_second=4, console=console) as live:
        for i in range(8):
            live.update(Align.center(f"[green]Initializing{'.' * (i % 4)}", vertical="middle"))
            time.sleep(0.2)

    console.print("[bold bright_cyan]Press [bold]Enter[/bold] to continue[/bold bright_cyan]", justify="center")
    input()

    # Initialize SAGE protocol
    sage = SAGE()

    # Prompt
    prompt = args.prompt or (
        "You are a consultant for a hospital planning to implement an AI-powered patient triage system. "
        "1. Identify the main ethical and operational challenges in deploying such a system. "
        "2. Suggest a technical architecture, including data sources, model types, and privacy safeguards. "
        "3. Draft a communication plan to explain the system to patients and staff, addressing concerns and highlighting benefits."
    )

    console.rule("[bold blue]SAGE Protocol: Sequential Agent Goal Execution[/bold blue]")
    console.print(Panel(prompt, title="[bold]Input Prompt[/bold]", style="cyan"))

    # Run the protocol with progress
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True, console=console) as progress:
        task = progress.add_task("Decomposing prompt...", total=None)
        subprompts = sage.decomposer.decompose(prompt)
        progress.update(task, description=f"Decomposed into {len(subprompts)} sub-prompts.")
        progress.stop_task(task)

        # Show sub-prompts
        table = Table(title="Sub-Prompts", box=box.SIMPLE, show_lines=True)
        table.add_column("#", style="bold")
        table.add_column("Content", style="white")
        table.add_column("Task Type", style="magenta")
        table.add_column("Expected Goal", style="green")
        for i, sp in enumerate(subprompts):
            table.add_row(str(i+1), sp.content, str(sp.task_type), sp.expected_goal)
        console.print(table)

        # Model assignment
        progress.start_task(task)
        assignments = []
        for i, subprompt in enumerate(subprompts):
            progress.update(task, description=f"Assigning model for SubPrompt {i+1}...")
            assignment = sage.router.route(subprompt)
            assignments.append(assignment)
        progress.update(task, description="Model assignment complete.")
        progress.stop_task(task)

        # Execution & evaluation
        results = []
        progress.start_task(task)
        for i, (subprompt, assignment) in enumerate(zip(subprompts, assignments)):
            progress.update(task, description=f"Executing SubPrompt {i+1} ({assignment.model_name})...")
            result = sage.executor.execute(subprompt, assignment)
            evaluation = sage.evaluator.evaluate(result, subprompt)
            results.append((subprompt, assignment, result, evaluation))
        progress.update(task, description="Execution and evaluation complete.")
        progress.stop_task(task)

    # Show results table
    console.rule("[bold green]Sub-Prompt Results[/bold green]")
    result_table = Table(box=box.MINIMAL_DOUBLE_HEAD)
    result_table.add_column("#", style="bold")
    result_table.add_column("Model", style="yellow")
    result_table.add_column("Success", style="green")
    result_table.add_column("Similarity", style="cyan")
    result_table.add_column("Content", style="white")
    for i, (subprompt, assignment, result, evaluation) in enumerate(results):
        result_table.add_row(
            str(i+1),
            assignment.model_name,
            "✅" if evaluation.success else "❌",
            f"{evaluation.similarity_score:.2f}",
            (result.content[:80] + ("..." if len(result.content) > 80 else ""))
        )
    console.print(result_table)

    # Show detailed output if verbose
    if args.verbose:
        for i, (subprompt, assignment, result, evaluation) in enumerate(results):
            console.rule(f"[bold]SubPrompt {i+1} Details[/bold]", style="blue")
            console.print(f"[bold]Prompt:[/bold] {subprompt.content}")
            console.print(f"[bold]Model:[/bold] {assignment.model_name}")
            console.print(f"[bold]Output:[/bold] {result.content}")
            console.print(f"[bold]Success:[/bold] {'✅' if evaluation.success else '❌'}")
            console.print(f"[bold]Similarity:[/bold] {evaluation.similarity_score:.2f}")
            console.print(f"[bold]Feedback:[/bold] {evaluation.feedback}")
            console.print("")

    # Aggregate and show final response
    agg = sage.aggregator.aggregate([r[2] for r in results])
    console.rule("[bold blue]Final Aggregated Response[/bold blue]")
    console.print(Panel(agg.final_response, title="[bold]Final Response[/bold]", style="green"))

    # Show metadata summary
    meta_table = Table(title="Run Metadata", box=box.SIMPLE)
    for k, v in agg.metadata.items():
        if k == "total_execution_time":
            # Format as mm:ss.s
            try:
                seconds = float(v)
                mins = int(seconds // 60)
                secs = seconds % 60
                formatted = f"{mins:02d}:{secs:05.2f} (raw: {seconds:.2f}s)"
                meta_table.add_row(str(k), formatted)
            except Exception:
                meta_table.add_row(str(k), str(v))
        else:
            meta_table.add_row(str(k), str(v))
    console.print(meta_table) 