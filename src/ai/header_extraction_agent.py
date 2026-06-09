import pandas as pd


class HeaderExtractionAgent:

    def extract_headers(self, file_path: str) -> list[str]:
        df = pd.read_csv(file_path)

        return list(df.columns)