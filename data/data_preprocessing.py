#!/usr/bin/env python3
"""
data_preprocessing.py
----------------------
Usage:
    1. Set your file path in the INPUT_FILE variable below
    2. Run: python data_preprocessing.py

This script:
 - Loads the Excel (.xlsx) file
 - Cleans and preprocesses data
 - Drops useless columns (high null ratio or metadata)
 - Fills missing values and cleans text fields
 - Creates a `combined_text` column for NLP/embedding tasks
 - Deduplicates rows by product Title + Vendor
 - Saves a cleaned CSV file next to the original file as *_cleaned.csv*
"""

import pandas as pd
import numpy as np
import re
import sys
import os
from pathlib import Path


# ========================================
# 📝 SET YOUR FILE PATH HERE
# ========================================
INPUT_FILE = r"assignment_docs\DermaGPT Product Database (1).xlsx"
# ========================================


# ---------- Helper Functions ----------


def clean_text(text):
    """Basic text cleaning: removes HTML tags, trims, collapses spaces."""
    if pd.isna(text):
        return ""
    s = str(text).strip()
    s = re.sub(r"<[^>]+>", "", s)  # remove HTML tags
    s = re.sub(r"\s+", " ", s)  # collapse whitespace
    s = re.sub(r"([?.!,;])\1+", r"\1", s)  # normalize punctuation
    return s


def preprocess_dermagpt(filepath: str):
    """Main function to preprocess DermaGPT Excel data and save cleaned CSV."""

    # ------------------ Step 1: Load ------------------
    print(f"📂 Loading file: {filepath}")
    df = pd.read_excel(filepath)
    print(f"✅ Loaded shape: {df.shape}")

    # ------------------ Step 2: Drop high-null columns ------------------
    null_pct = df.isnull().mean() * 100
    high_null_cols = null_pct[null_pct > 80].index.tolist()

    manual_drop = [
        "Metafield: shopify--discovery--product_recommendation.related_products",
        "Metafield: shopify--discovery--product_recommendation.related_products_display",
        "Metafield: shopify--discovery--product_recommendation.complementary_products",
        "Metafield: custom.video_consult_template",
        "Metafield: custom.video_consult_banner_images",
        "Metafield: custom.video_consult_form_heading",
        "Metafield: custom.video_consult_sub_heading",
        "Metafield: custom.pdp_social_videos",
        "Metafield: custom.marketer_metaobject",
        "Metafield: shopify.target-gender",
        "Metafield: custom.usp_icons",
        "Metafield: shopify.product-certifications-standards",
        "Metafield: custom.contraindications",
        "Metafield: custom.active_offers",
    ]
    drop_cols = list(set(high_null_cols + [c for c in manual_drop if c in df.columns]))
    df.drop(columns=drop_cols, inplace=True, errors="ignore")
    print(
        f"🧹 Dropped {len(drop_cols)} columns (high null / irrelevant). Remaining: {df.shape[1]}"
    )

    # ------------------ Step 3: Fill key missing values ------------------
    fill_map = {
        "D": "Description not available",
        "Metafield: my_fields.brand_name": "Unknown Brand",
        "Metafield: reviews.rating": np.nan,
        "Metafield: reviews.rating_count": 0,
    }
    for col, val in fill_map.items():
        if col in df.columns:
            df[col] = df[col].fillna(val)

    # Convert numeric ratings properly
    if "Metafield: reviews.rating" in df.columns:
        df["Metafield: reviews.rating"] = pd.to_numeric(
            df["Metafield: reviews.rating"], errors="coerce"
        )
    if "Metafield: reviews.rating_count" in df.columns:
        df["Metafield: reviews.rating_count"] = (
            pd.to_numeric(df["Metafield: reviews.rating_count"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    # ------------------ Step 4: Clean text columns ------------------
    text_cols = [c for c in df.columns if df[c].dtype == "object"]
    for c in text_cols:
        df[c] = df[c].apply(clean_text)

    # ------------------ Step 5: Create combined_text ------------------
    combine_order = [
        "Title",
        "D",
        "Metafield: my_fields.brand_name",
        "Metafield: my_fields.subtitle",
        "Metafield: custom.key_benefits_list",
        "Metafield: custom.key_ingredients_list",
        "Metafield: custom.uses_list",
        "Metafield: custom.skin_concerns",
        "Tags",
    ]
    existing = [c for c in combine_order if c in df.columns]

    df["combined_text"] = df[existing].astype(str).agg(" | ".join, axis=1)
    print("🧠 Created `combined_text` column.")

    # ------------------ Step 6: Deduplicate ------------------
    subset_cols = [c for c in ["Title", "Vendor", "Variant Price"] if c in df.columns]
    before = len(df)
    df.drop_duplicates(subset=subset_cols, inplace=True)
    after = len(df)
    print(f"🧩 Deduplicated: {before - after} duplicates removed. Final rows: {after}")

    # ------------------ Step 7: Save cleaned CSV ------------------
    out_path = Path(filepath).with_name(Path(filepath).stem + "_cleaned.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"✅ Cleaned CSV saved to: {out_path}")
    print(f"Final shape: {df.shape}")


# ---------- Main Entry ----------
if __name__ == "__main__":
    # Check if file exists
    if not os.path.exists(INPUT_FILE):
        print(f"❌ File not found: {INPUT_FILE}")
        print(
            "💡 Please update the INPUT_FILE variable at the top of this script with the correct path."
        )
        sys.exit(1)

    # Run preprocessing
    preprocess_dermagpt(INPUT_FILE)
