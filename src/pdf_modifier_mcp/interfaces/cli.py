"""
CLI interface for PDF Modifier.

Human-friendly command-line interface with colored output.
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.table import Table

from ..core.analyzer import PDFAnalyzer
from ..core.exceptions import PDFModifierError
from ..core.models import ReplacementSpec
from ..core.modifier import PDFModifier, batch_process
from ..logger import setup_logging


def _parse_custom_fonts(ctx: Any, fonts: list[str] | None) -> dict[str, str] | None:
    """Parse --custom-fonts KEY=PATH options into a dict."""
    if not fonts:
        return None
    result: dict[str, str] = {}
    for item in fonts:
        if "=" not in item:
            console.print(
                f"[red]Error:[/] Invalid custom font format '{item}'. "
                f"Use 'alias=/path/to/font.ttf'."
            )
            raise typer.Exit(code=1)
        alias, path = item.split("=", 1)
        result[alias] = path
    return result


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
    pages: Annotated[
        str | None,
        typer.Option(
            "--pages",
            "-P",
            help="Page range to process, e.g. '1-3' or '5'. Defaults to all pages.",
        ),
    ] = None,
    custom_fonts: Annotated[
        list[str] | None,
        typer.Option(
            "--custom-fonts",
            help="Custom font mapping. Format: 'alias=/path/to/font.ttf'. Repeatable.",
        ),
    ] = None,
) -> None:
    """
    Modify a PDF by finding and replacing text while preserving font style.

    Examples:
        pdf-mod modify input.pdf output.pdf -r "old text=new text"
        pdf-mod modify input.pdf output.pdf -r "$99.99=$149.99" --regex
        pdf-mod modify input.pdf output.pdf -r "Click Here=Visit Site|https://example.com"
        pdf-mod modify input.pdf output.pdf -r "Hello=Hi" --pages 1-3
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

    page_range: tuple[int, int] | None = None
    if pages:
        parts = pages.split("-")
        if len(parts) == 1:
            try:
                page_range = (int(parts[0]), int(parts[0]))
            except ValueError:
                console.print(f"[red]Error:[/] Invalid page number: '{parts[0]}'")
                raise typer.Exit(code=1) from None
        elif len(parts) == 2:
            try:
                start, end = int(parts[0]), int(parts[1])
                page_range = (start, end)
            except ValueError:
                console.print(f"[red]Error:[/] Invalid page range: '{pages}'")
                raise typer.Exit(code=1) from None
        else:
            console.print(f"[red]Error:[/] Invalid page range format: '{pages}'. Use '1-3' or '5'.")
            raise typer.Exit(code=1)

    try:
        spec = ReplacementSpec(replacements=replacements, use_regex=regex)
        cf = _parse_custom_fonts(None, custom_fonts) if custom_fonts else None
        modifier = PDFModifier(
            str(input_pdf.absolute()),
            str(output_pdf.absolute()),
            password=password,
            custom_fonts=cf,
        )

        with console.status("[bold green]Modifying PDF...", spinner="dots"):
            result = modifier.process(spec, pages=page_range)

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
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(code=1) from None
    except Exception:
        logger.exception("Unexpected error in CLI modify")
        console.print("[red]Error:[/] An unexpected error occurred. Check logs.")
        raise typer.Exit(code=1) from None


@app.command()
def batch(
    input_pdfs: Annotated[
        list[Path],
        typer.Argument(help="Paths to input PDF files"),
    ],
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", "-o", help="Directory for modified PDFs"),
    ],
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
        typer.Option("--regex", help="Treat 'old' values as regex"),
    ] = False,
    password: Annotated[
        str | None,
        typer.Option("--password", "-p", help="Password if PDFs are encrypted"),
    ] = None,
    custom_fonts: Annotated[
        list[str] | None,
        typer.Option(
            "--custom-fonts",
            help="Custom font mapping. Format: 'alias=/path/to/font.ttf'. Repeatable.",
        ),
    ] = None,
) -> None:
    """
    Apply the same replacements to multiple PDF files.

    Processes each file independently. Failed files do not stop the batch.
    Output files are saved to --output-dir with the same filename.

    Examples:
        pdf-mod batch a.pdf b.pdf -o out/ -r "Draft=Final"
        pdf-mod batch *.pdf -o out/ -r "2024=2025" -r "old=new"
    """
    replacements: dict[str, str] = {}
    for item in replace:
        if "=" not in item:
            console.print(
                f"[yellow]Warning:[/] Skipping invalid format" f" '{item}'. Use 'old=new'."
            )
            continue
        old, new = item.split("=", 1)
        replacements[old] = new

    if not replacements:
        console.print("[red]Error:[/] No valid replacements provided.")
        raise typer.Exit(code=1)

    try:
        spec = ReplacementSpec(replacements=replacements, use_regex=regex)
        cf = _parse_custom_fonts(None, custom_fonts) if custom_fonts else None

        with console.status("[bold green]Processing batch...", spinner="dots"):
            result = batch_process(
                input_pdfs,
                output_dir,
                spec,
                password=password,
                custom_fonts=cf,
            )

        table = Table(title="Batch Results")
        table.add_column("File", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Replacements")

        for res in result.results:
            table.add_row(
                res.input_path,
                "OK",
                str(res.replacements_made),
            )
        for err in result.errors:
            table.add_row(err["file"], f"[red]{err['error']}[/]", "-")

        console.print(table)
        console.print(
            f"\n[bold]{result.successful} succeeded[/],"
            f" [bold]{result.failed} failed[/]"
            f" out of {result.total_files} files."
        )

    except PDFModifierError as e:
        logger.error("Batch error: %s", e.message)
        console.print(f"[red]Error:[/] {e.message}")
        raise typer.Exit(code=1) from None
    except Exception:
        logger.exception("Unexpected error in CLI batch")
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
