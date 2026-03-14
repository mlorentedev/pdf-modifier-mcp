"""
CLI interface for PDF Modifier.

Human-friendly command-line interface with colored output.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from ..core.analyzer import PDFAnalyzer
from ..core.exceptions import PDFModifierError
from ..core.models import ReplacementSpec
from ..core.modifier import PDFModifier
from ..logger import setup_logging

logger = setup_logging(__name__)

app = typer.Typer(
    name="pdf-mod",
    help="PDF Modifier - Find and replace text in PDFs while preserving style.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def modify(
    input_pdf: Annotated[Path, typer.Argument(help="Path to input PDF")],
    output_pdf: Annotated[Path, typer.Argument(help="Path to output PDF")],
    replace: Annotated[
        list[str],
        typer.Option(
            "--replace",
            "-r",
            help="Format: 'old=new'. Use '|url' suffix for links.",
        ),
    ],
    regex: Annotated[
        bool,
        typer.Option("--regex", help="Treat 'old' values as regex patterns"),
    ] = False,
    password: Annotated[
        str | None,
        typer.Option("--password", "-p", help="Password if PDF is encrypted"),
    ] = None,
) -> None:
    """
    Modify a PDF by finding and replacing text while preserving font style.

    Examples:
        pdf-mod modify input.pdf output.pdf -r "old text=new text"
        pdf-mod modify input.pdf output.pdf -r "$99.99=$149.99" --regex
        pdf-mod modify input.pdf output.pdf -r "Click Here=Visit Site|https://example.com"
    """
    replacements = {}
    for item in replace:
        if "=" not in item:
            console.print(f"[yellow]Warning:[/] Skipping invalid format '{item}'. Use 'old=new'.")
            continue
        old, new = item.split("=", 1)
        replacements[old] = new

    if not replacements:
        console.print("[red]Error:[/] No valid replacements provided.")
        raise typer.Exit(code=1)

    try:
        spec = ReplacementSpec(replacements=replacements, use_regex=regex)
        modifier = PDFModifier(
            str(input_pdf.absolute()),
            str(output_pdf.absolute()),
            password=password,
        )

        with console.status("[bold green]Modifying PDF...", spinner="dots"):
            result = modifier.process(spec)

        console.print(f"[green]Success:[/] Saved to {result.output_path}")
        console.print(f"  Replacements: {result.replacements_made}")
        console.print(f"  Pages modified: {result.pages_modified}")

        if result.warnings:
            for warn in result.warnings:
                console.print(f"[yellow]Warning:[/] {warn}")

    except PDFModifierError as e:
        logger.error(f"Modification error: {e.message}")
        console.print(f"[red]Error:[/] {e.message}")
        raise typer.Exit(code=1) from None
    except Exception:
        logger.exception("Unexpected error in CLI modify")
        console.print("[red]Error:[/] An unexpected error occurred. Check logs.")
        raise typer.Exit(code=1) from None


@app.command()
def analyze(
    input_pdf: Annotated[Path, typer.Argument(help="Path to input PDF")],
    json_output: Annotated[
        bool,
        typer.Option("--json", "-j", help="Output as JSON structure"),
    ] = False,
    password: Annotated[
        str | None,
        typer.Option("--password", "-p", help="Password if PDF is encrypted"),
    ] = None,
) -> None:
    """
    Extract text or structure from a PDF.

    Use --json for machine-readable output with positions and fonts.
    """
    try:
        analyzer = PDFAnalyzer(str(input_pdf.absolute()), password=password)

        if json_output:
            result = analyzer.get_structure()
            console.print_json(result.model_dump_json(indent=2))
        else:
            console.print(analyzer.extract_text())

    except PDFModifierError as e:
        logger.error("Analysis error: %s", e.message)
        console.print(f"[red]Error:[/] {e.message}")
        raise typer.Exit(code=1) from None
    except Exception:
        logger.exception("Unexpected error in CLI analyze")
        console.print("[red]Error:[/] An unexpected error occurred. Check logs.")
        raise typer.Exit(code=1) from None


@app.command()
def inspect(
    input_pdf: Annotated[Path, typer.Argument(help="Path to input PDF")],
    terms: Annotated[list[str], typer.Argument(help="Terms to search for")],
    password: Annotated[
        str | None,
        typer.Option("--password", "-p", help="Password if PDF is encrypted"),
    ] = None,
) -> None:
    """
    Inspect font properties for specific terms in a PDF.

    Useful for understanding font styles before making replacements.
    """
    try:
        analyzer = PDFAnalyzer(str(input_pdf.absolute()), password=password)
        result = analyzer.inspect_fonts(terms)

        if not result.matches:
            console.print("[yellow]No matches found.[/]")
            return

        table = Table(title=f"Font Inspection: {input_pdf.name}")
        table.add_column("Page", style="cyan")
        table.add_column("Term", style="green")
        table.add_column("Font")
        table.add_column("Size")
        table.add_column("Context")

        for match in result.matches:
            context = match.context[:40] + "..." if len(match.context) > 40 else match.context
            table.add_row(
                str(match.page),
                match.term,
                match.font,
                f"{match.size:.1f}",
                context,
            )

        console.print(table)

    except PDFModifierError as e:
        logger.error("Inspection error: %s", e.message)
        console.print(f"[red]Error:[/] {e.message}")
        raise typer.Exit(code=1) from None
    except Exception:
        logger.exception("Unexpected error in CLI inspect")
        console.print("[red]Error:[/] An unexpected error occurred. Check logs.")
        raise typer.Exit(code=1) from None


@app.command()
def links(
    input_pdf: Annotated[Path, typer.Argument(help="Path to input PDF")],
    password: Annotated[
        str | None,
        typer.Option("--password", "-p", help="Password if PDF is encrypted"),
    ] = None,
) -> None:
    """
    List all hyperlinks found in a PDF document.
    """
    try:
        analyzer = PDFAnalyzer(str(input_pdf.absolute()), password=password)
        result = analyzer.get_hyperlinks()

        if not result.links:
            console.print("[yellow]No hyperlinks found.[/]")
            return

        table = Table(title=f"Hyperlink Inventory: {input_pdf.name}")
        table.add_column("Page", style="cyan")
        table.add_column("URI", style="green")
        table.add_column("Text Area", style="magenta")

        for link in result.links:
            text_raw = link.text or "-"
            text = text_raw[:50] + "..." if len(text_raw) > 50 else text_raw
            table.add_row(
                str(link.page),
                link.uri,
                text,
            )

        console.print(table)
        console.print(f"\n[bold green]✔[/] Found [bold]{result.total_links}[/] links in total.")

    except PDFModifierError as e:
        logger.error("Links error: %s", e.message)
        console.print(f"[red]Error:[/] {e.message}")
        raise typer.Exit(code=1) from None
    except Exception:
        logger.exception("Unexpected error in CLI links")
        console.print("[red]Error:[/] An unexpected error occurred. Check logs.")
        raise typer.Exit(code=1) from None


def main() -> None:
    """Entry point for CLI."""
    app()


if __name__ == "__main__":
    main()
