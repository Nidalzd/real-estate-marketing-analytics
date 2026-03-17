# Notebook Rules

Notebooks are numbered 01-08 and must execute in sequence. Never create a notebook that depends on a higher-numbered notebook.

Every notebook must:
1. Start with `os.chdir('..')` to set project root as working directory
2. Use `sys.path.insert(0, '.')` for src module imports
3. Have markdown narrative between every code cell
4. Write business insights, not data descriptions
5. Call `save_fig()` on every chart to export to `reports/figures/`
6. End with a "Key Takeaways" markdown summary

When creating notebooks programmatically, use `nbformat` and verify execution with `jupyter nbconvert --execute`.

Never leave a notebook in a state where it fails to execute top-to-bottom.
