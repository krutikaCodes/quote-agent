import sys
import pdfplumber
import pandas as pd
import os


def read_services_pdf(pdf_file):
    """
    Read Services.pdf
    Returns DataFrame:
    Services | Qty | Unit Price
    """

    records = []

    with pdfplumber.open(pdf_file) as pdf:

        for page in pdf.pages:

            tables = page.extract_tables()

            for table in tables:

                if len(table) < 2:
                    continue

                for row in table[1:]:

                    try:
                        service = str(row[0]).strip()

                        qty = int(
                            str(row[1])
                            .replace(",", "")
                            .strip()
                        )

                        unit_price = float(
                            str(row[2])
                            .replace("$", "")
                            .replace(",", "")
                            .strip()
                        )

                        records.append({
                            "Services": service,
                            "Qty": qty,
                            "Unit Price": unit_price
                        })

                    except Exception:
                        print(f"Skipping row: {row}")
                        continue

    return pd.DataFrame(records)


def read_standard_excel(excel_file):
    """
    Read Standard.xlsx
    Returns:
    Services | Unit Cost
    """

    df = pd.read_excel(
        excel_file,
        engine="openpyxl"
    )

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    required_columns = [
        "Services",
        "Unit Cost"
    ]

    missing = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required columns: {missing}"
        )

    return df[required_columns]


def create_output(
    services_df,
    standard_df
):
    """
    Merge and calculate output
    """

    final_df = pd.merge(
        services_df,
        standard_df,
        on="Services",
        how="left"
    )

    final_df["Unit Cost"] = (
        final_df["Unit Cost"]
        .fillna(0)
    )

    final_df["Ext. Price"] = (
        final_df["Qty"]
        * final_df["Unit Price"]
    )

    final_df["Ext. Cost"] = (
        final_df["Qty"]
        * final_df["Unit Cost"]
    )

    final_df["Margin $"] = (
        final_df["Ext. Price"]
        - final_df["Ext. Cost"]
    )

    final_df["Margin %"] = (
        final_df["Margin $"]
        / final_df["Ext. Price"]
    ).fillna(0)

    return final_df


def add_totals_row(final_df):

    total_price = final_df["Ext. Price"].sum()
    total_cost = final_df["Ext. Cost"].sum()
    total_margin = final_df["Margin $"].sum()

    if total_price > 0:
        total_margin_pct = (
            total_margin
            / total_price
        )
    else:
        total_margin_pct = 0

    total_row = pd.DataFrame([
        {
            "Services": "Monthly Services",
            "Qty": "",
            "Unit Price": "",
            "Unit Cost": "",
            "Ext. Price": total_price,
            "Ext. Cost": total_cost,
            "Margin $": total_margin,
            "Margin %": total_margin_pct
        }
    ])

    final_df = pd.concat(
        [final_df, total_row],
        ignore_index=True
    )

    return final_df


def write_excel(
    final_df,
    output_file
):

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl"
    ) as writer:

     
