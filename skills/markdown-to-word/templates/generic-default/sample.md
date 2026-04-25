# Sample Report

**Title**: Sample Report for Markdown to Word

**Abstract**:

This sample document demonstrates headings, lists, code blocks, captions, and references.

**Keywords**: Markdown; DOCX; Pandoc; Template

## Summary

The pipeline should normalize lightweight list formatting before Word conversion.

1. Collect the manuscript.
2. Normalize Markdown where needed.
3. Convert with Pandoc.

## Architecture

```python
def greet(name: str) -> str:
    return f"Hello, {name}!"
```

```mermaid
flowchart LR
    Markdown --> Pandoc --> DOCX
```

Figure 1-1 Conversion Flow

## References

[1] Pandoc User Guide.
[2] python-docx Documentation.
