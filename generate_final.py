import sys
import pdfplumber
import pandas as pd
import os


def read_services_pdf(pdf_file):
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

                        records.append(
                            {
                                "Services": service,
                                "Qty": qty,
                                "Unit Price": unit_price
                            }
                        )

                    except Exception:
                        continue

    return pd.DataFrame(records)


def read_standard_excel(excel_file):

    df = pd.read_excel(
        excel_file,
        engine="openpyxl"
    )

    df.columns = [
        str(col).strip()
        for col in df.columns
    ]

    return df[
        [
            "Services",
            "Unit Cost"
        ]
    ]


def create_output(
    services_df,
    standard_df
):

    final_df = pd.merge(
        services_df,
        standard_df,
        on="Services",
        how="left"
    )

    final_df["Unit Cost"] = final_df["Unit Cost"].fillna(0)

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
            total_margin / total_price
        )
    else:
        total_margin_pct = 0

    totals = pd.DataFrame(
        [
            {
                "Services": "Monthly Services",
                "Qty": "",
                "Unit Price": "",
                "Unit Cost": "",
                "Ext. Price": total_price,
                "Ext. Cost": total_cost,
                "Margin $": total_margin,
                "Margin %": total_margin_pct,
            }
        ]
    )

    return pd.concat(
        [final_df, totals],
        ignore_index=True
    )


def write_excel(final_df, output_file):

    with pd.ExcelWriter(
        output_file,
        engine="openpyxl"
    ) as writer:

        final_df.to_excel(
            writer,
            sheet_name="Final Output",
            index=False
        )

        worksheet = writer.sheets[
            "Final Output"
        ]

        for row in range(
            2,
            len(final_df) + 2
        ):
            worksheet[f"H{row}"].number_format = "0.00%"

        for column in worksheet.columns:

            max_length = 0
            column_letter = column[0].column_letter

            for cell in column:
                try:
                    max_length = max(
                        max_length,
                        len(str(cell.value))
                    )
                except Exception:
                    pass

            worksheet.column_dimensions[
                column_letter
            ].width = max_length + 3


def main():

    print("STARTING SCRIPT")

    if len(sys.argv) != 4:
        print(
            "Usage: python generate_final.py "
            "<services.pdf> "
            "<standard.xlsx> "
            "<output.xlsx>"
        )
        sys.exit(1)

    pdf_file = sys.argv[1]
    standard_file = sys.argv[2]
    output_file = sys.argv[3]

    print("ABOUT TO READ PDF")
    services_df = read_services_pdf(pdf_file)
    print("PDF READ COMPLETE")

    print("ABOUT TO READ EXCEL")
    standard_df = read_standard_excel(
        standard_file
    )
    print("EXCEL READ COMPLETE")

    print("CALCULATING")
    final_df = create_output(
        services_df,
        standard_df
    )

    final_df = add_totals_row(
        final_df
    )

    output_dir = os.path.dirname(output_file)

    if output_dir:
        os.makedirs(
            output_dir,
            exist_ok=True
        )

    print("ABOUT TO WRITE OUTPUT")

    write_excel(
        final_df,
        output_file
    )

    print("DONE")
    print(output_file)


if __name__ == "__main__":
    main()
