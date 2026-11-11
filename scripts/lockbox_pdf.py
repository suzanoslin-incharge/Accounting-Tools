"""Read a daily lockbox PDF: header text, items and page images.

The text line at the top of every page gives value date, program, batch, item
and (on the check page) the check number and amount. This module reads that
text, groups the pages of each item, and renders page images. The payer name and
invoice numbers exist only in the images; the agent reads them from the images.
Nothing here uses OCR and nothing here talks to BC.

Usage:
    python3 lockbox_pdf.py "Lockbox 2026.10.01.pdf" [--images DIR] [--bank-total 16362.68]
"""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

import pdfplumber

HEADER_RE = re.compile(
    r"Value Date:\s*(?P<date>\d{2}/\d{2}/\d{4})\s+Program:\s*(?P<program>.+?)\s+"
    r"Batch Number:\s*(?P<batch>\d+)\s+Item Number:\s*(?P<item>\d+)", re.S)
PAYMENT_RE = re.compile(
    r"Payment Serial Number:\s*(?P<check>\S+)\s+Amount:\s*(?P<cur>[A-Z]{3})\s*(?P<amt>[\d,]+\.\d{2})")


@dataclass
class LockboxItem:
    batch: str
    item: int
    value_date: str            # yyyy-mm-dd
    program: str
    check_no: str = ""
    currency: str = ""
    amount: Decimal = Decimal("0")
    pages: List[int] = field(default_factory=list)       # 1-based page numbers
    images: List[str] = field(default_factory=list)      # image files, same order


def read_items(pdf_path: str) -> List[LockboxItem]:
    """One LockboxItem per item number; pages are grouped by the header text."""
    items = {}
    with pdfplumber.open(pdf_path) as pdf:
        for n, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            h = HEADER_RE.search(text)
            if not h:
                raise ValueError(f"Page {n}: no header text found. Read this page by hand.")
            key = (h["batch"], int(h["item"]))
            if key not in items:
                d = dt.datetime.strptime(h["date"], "%m/%d/%Y").date().isoformat()
                items[key] = LockboxItem(h["batch"], int(h["item"]), d, h["program"].strip())
            it = items[key]
            it.pages.append(n)
            p = PAYMENT_RE.search(text)
            if p:
                it.check_no, it.currency = p["check"], p["cur"]
                it.amount = Decimal(p["amt"].replace(",", ""))
    return sorted(items.values(), key=lambda i: (i.batch, i.item))


def render_images(pdf_path: str, items: List[LockboxItem], out_dir: str, dpi: int = 150) -> None:
    """Render every page to PNG (pdftoppm) and record the file names on each item."""
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    stem = out / "page"
    subprocess.run(["pdftoppm", "-r", str(dpi), "-png", pdf_path, str(stem)], check=True)
    files = {int(re.search(r"-(\d+)\.png$", f.name).group(1)): str(f) for f in out.glob("page-*.png")}
    for it in items:
        it.images = [files[p] for p in it.pages]


def tie_out(items: List[LockboxItem], bank_total: Optional[Decimal]) -> dict:
    """The lockbox total must equal the bank amount."""
    total = sum((i.amount for i in items), Decimal("0"))
    missing = [i.item for i in items if not i.check_no or i.amount == 0]
    ok = bank_total is not None and total == bank_total and not missing
    return {"total": str(total), "bank_total": None if bank_total is None else str(bank_total),
            "ties": ok, "items_without_check_data": missing}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("--images"); ap.add_argument("--bank-total")
    a = ap.parse_args(argv)
    items = read_items(a.pdf)
    if a.images:
        render_images(a.pdf, items, a.images)
    bank = Decimal(a.bank_total) if a.bank_total else None
    print(json.dumps({"items": [asdict(i) for i in items], "tie_out": tie_out(items, bank)},
                     indent=2, default=str))


if __name__ == "__main__":
    main()
