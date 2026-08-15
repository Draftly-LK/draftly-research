"""Layout-aware parsers for the CommonLII LKSC HTML archive.

Pipeline:
1. ``split_categories.py`` splits ``data/commonlii/layout-categories.json``
   into one JSON per layout category plus ``uncertain.json``.
2. ``parse_archive.py`` parses every judgment with the parser registered for
   its layout and writes one CSV per category plus a combined main CSV.
"""
