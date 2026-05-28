from pathlib import Path
import tempfile

import streamlit as st

from parsers.csv_parser import parse_erp_orders_csv
from parsers.rest_api_parser import parse_api_orders
from transformers.wms_xml_transformer import export_orders_to_xml
import json


st.set_page_config(
    page_title="Modula WMS Integration Agent",
    layout="wide",
)

st.title("Modula WMS Integration Agent")
st.write("Convert ERP CSV or REST API JSON data into Modula WMS XML.")

input_type = st.selectbox(
    "Choose input type",
    ["CSV Order Header + Line Files", "REST API JSON File"],
)

output_dir = Path("data/output")
output_dir.mkdir(parents=True, exist_ok=True)

if input_type == "CSV Order Header + Line Files":
    header_file = st.file_uploader("Upload order header CSV", type=["csv"])
    line_file = st.file_uploader("Upload order line CSV", type=["csv"])

    if st.button("Convert CSV to WMS XML"):
        if not header_file or not line_file:
            st.error("Please upload both header and line CSV files.")
        else:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_header:
                temp_header.write(header_file.read())
                header_path = temp_header.name

            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as temp_line:
                temp_line.write(line_file.read())
                line_path = temp_line.name

            orders = parse_erp_orders_csv(header_path, line_path)

            output_path = output_dir / "ui_csv_orders_wms.xml"
            export_orders_to_xml(orders, str(output_path))

            xml_content = output_path.read_text(encoding="utf-8")

            st.success(f"Converted {len(orders)} orders.")
            st.code(xml_content, language="xml")

            st.download_button(
                "Download WMS XML",
                data=xml_content,
                file_name="csv_orders_wms.xml",
                mime="application/xml",
            )

if input_type == "REST API JSON File":
    json_file = st.file_uploader("Upload REST API JSON response", type=["json"])

    if st.button("Convert JSON to WMS XML"):
        if not json_file:
            st.error("Please upload a JSON file.")
        else:
            api_data = json.load(json_file)

            orders = parse_api_orders(api_data)

            output_path = output_dir / "ui_api_orders_wms.xml"
            export_orders_to_xml(orders, str(output_path))

            xml_content = output_path.read_text(encoding="utf-8")

            st.success(f"Converted {len(orders)} orders.")
            st.code(xml_content, language="xml")

            st.download_button(
                "Download WMS XML",
                data=xml_content,
                file_name="api_orders_wms.xml",
                mime="application/xml",
            )