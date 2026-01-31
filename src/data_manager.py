import json
import pandas as pd
from datetime import datetime
from pathlib import Path
from fpdf import FPDF


class DataManager:
    def __init__(self):
        self.src_dir = Path(__file__).resolve().parent
        self.fonts_dir = self.src_dir / "fonts"
        self.base_dir = self.src_dir.parent
        self.data_dir = self.base_dir / "data"

        self.inputs_dir = self.data_dir / "inputs"
        self.results_dir = self.data_dir / "results"
        self.reports_dir = self.data_dir / "reports"
        self.history_file = self.data_dir / "history.json"

        for folder in [self.inputs_dir, self.results_dir, self.reports_dir]:
            folder.mkdir(parents=True, exist_ok=True)

        if not self.history_file.exists():
            with open(self.history_file, "w", encoding="utf-8") as f:
                json.dump([], f)

    def save_record(self, filename, total_moto, violations):
        history = self.load_history()
        new_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "filename": filename,
            "total": total_moto,
            "violations": violations,
        }
        history.append(new_record)
        with open(self.history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)

    def load_history(self):
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def get_report_path(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return str(self.reports_dir / f"report_{timestamp}.pdf")

    def generate_pdf(self):
        history = self.load_history()
        report_path = self.get_report_path()

        pdf = FPDF()
        pdf.add_page()

        font_path = self.fonts_dir / "LiberationSerif-Regular.ttf"

        FONT_NAME = "LiberationSerif"

        if font_path.exists():
            pdf.add_font(FONT_NAME, style="", fname=str(font_path))
            pdf.set_font(FONT_NAME, size=14)
        else:
            pdf.set_font("Helvetica", size=14)
            print(f"Warning: Font not found at {font_path}")

        line_h = 10

        pdf.cell(
            0, line_h, txt="Отчет системы мониторинга полосы ОТ", ln=True, align="C"
        )
        pdf.ln(5)

        pdf.set_font(FONT_NAME, size=10)
        pdf.set_fill_color(230, 230, 230)
        pdf.cell(45, line_h, "Дата/Время", border=1, fill=True, align="C")
        pdf.cell(80, line_h, "Файл", border=1, fill=True, align="C")
        pdf.cell(30, line_h, "Всего мото", border=1, fill=True, align="C")
        pdf.cell(35, line_h, "Нарушения", border=1, fill=True, align="C")
        pdf.ln()

        pdf.set_font(FONT_NAME, size=12)
        for row in history:
            ts = str(row.get("timestamp", ""))
            fn = str(row.get("filename", ""))[:25]
            tot = str(row.get("total", "0"))
            viol = str(row.get("violations", "0"))

            pdf.cell(45, line_h, ts, border=1, align="C")
            pdf.cell(80, line_h, fn, border=1)
            pdf.cell(30, line_h, tot, border=1, align="C")
            pdf.cell(35, line_h, viol, border=1, align="C")
            pdf.ln()

        pdf.output(report_path)
        return report_path

    def generate_xlsx(self):
        history = self.load_history()
        if not history:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.reports_dir / f"report_{timestamp}.xlsx"

        df = pd.DataFrame(history)

        df.columns = [
            "Дата и время",
            "Имя файла",
            "Всего мотоциклов",
            "Нарушений в ЗОТ",
        ]

        df.to_excel(report_path, index=False, engine="openpyxl")

        return str(report_path)
