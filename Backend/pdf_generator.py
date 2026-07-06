import os
from datetime import datetime
from fpdf import FPDF

class DiagnosticReportPDF(FPDF):
    def header(self):
        self.set_fill_color(11, 19, 43)
        self.rect(0, 0, 210, 38, 'F')
        
        self.set_text_color(6, 182, 212)
        self.set_font("helvetica", "B", 20)
        self.set_xy(15, 10)
        self.cell(0, 8, "Tremor Plot", ln=1)
        
        self.set_text_color(203, 213, 225)
        self.set_font("helvetica", "", 10)
        self.set_x(15)
        self.cell(0, 5, "Parkinson's Screening Support System (Webcam & Sensor-Fusion)", ln=1)
        self.set_text_color(203, 213, 225)
        self.set_font("helvetica", "I", 9)
        self.set_xy(145, 12)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cell(50, 5, f"Generated: {current_time}", align="R", ln=1)
        self.set_xy(145, 17)
        self.cell(50, 5, "Report ID: TP-" + datetime.now().strftime("%Y%m%d%H%M"), align="R")
        
        self.ln(20)

    def footer(self):
        self.set_draw_color(30, 41, 59)
        self.set_line_width(0.5)
        self.line(15, 275, 195, 275)
        
        self.set_y(-18)
        self.set_font("helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 4, "Disclaimer: Not a clinical diagnosis system. Abnormal signals require medical consulting.", align="C", ln=1)
        
        self.set_y(-12)
        self.set_font("helvetica", "", 8)
        self.cell(0, 4, f"Page {self.page_no()} of {{nb}}", align="C")

def get_severity_colors(severity):
    severity = severity.strip().capitalize()
    if severity == "Normal":
        return (16, 185, 129), (209, 250, 229)
    elif severity == "Mild":
        return (6, 182, 212), (207, 250, 254)
    elif severity == "Moderate":
        return (245, 158, 11), (254, 243, 199)
    elif severity == "Severe":
        return (239, 68, 68), (254, 226, 226)
    return (100, 116, 139), (241, 245, 249)

def generate_screening_pdf(data: dict) -> str:
    pdf = DiagnosticReportPDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    pdf.set_y(48)
    pdf.set_text_color(11, 19, 43)
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 6, "1. Patient Profile", ln=1)

    pdf.set_draw_color(11, 19, 43)
    pdf.set_line_width(0.8)
    pdf.line(15, 55, 195, 55)
    pdf.ln(3)
    
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(15, 57, 180, 28, 'F')
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(100, 116, 139)
    
    pdf.set_xy(18, 60)
    pdf.cell(30, 6, "Patient Name:")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(60, 6, str(data.get("patientName") or "Unknown Patient"))
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(30, 6, "Patient ID:")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(50, 6, str(data.get("patientID") or "Unknown ID"), ln=1)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.set_x(18)
    pdf.cell(30, 6, "Age:")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(60, 6, f"{data.get('patientAge') or 'N/A'} Years")
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(30, 6, "Screening Date:")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(50, 6, datetime.now().strftime("%Y-%m-%d"), ln=1)
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.set_x(18)
    pdf.cell(30, 6, "Testing Hand:")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(60, 6, f"{data.get('selectedHand', 'Right')} Hand")
    
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(30, 6, "Hardware Status:")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(15, 23, 42)
    status_text = "Connected (ESP32 Sensor)" if data.get("isEspConnected") else "Simulated Sensor"
    pdf.cell(50, 6, status_text, ln=1)
    
    pdf.ln(12)
    
    pdf.set_text_color(11, 19, 43)
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 6, "2. Clinical Diagnostics Summary", ln=1)
    
    pdf.line(15, 96, 195, 96)
    pdf.ln(3)
    
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(15, 98, 88, 32, 'F')
    pdf.rect(107, 98, 88, 32, 'F')

    pdf.set_xy(18, 101)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(82, 5, "DOMINANT TREMOR FREQUENCY", ln=1)
    pdf.set_x(18)
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(6, 182, 212)
    freq = float(data.get("currentFreq", 0.0))
    pdf.cell(82, 10, f"{freq:.2f} Hz", ln=1)
    pdf.set_x(18)
    pdf.set_font("helvetica", "I", 8.5)
    pdf.set_text_color(71, 85, 105)
    freq_desc = "Parkinsonian Rest Range (4-6 Hz)" if 4.0 <= freq <= 6.0 else "Essential/Physiological (8-12 Hz)" if 8.0 <= freq <= 12.0 else "Normal/Physiological Range"
    pdf.cell(82, 5, freq_desc)

    pdf.set_xy(110, 101)
    pdf.set_font("helvetica", "B", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(82, 5, "TREMOR INTENSITY (RMS AMPLITUDE)", ln=1)
    pdf.set_x(110)
    pdf.set_font("helvetica", "B", 16)
    pdf.set_text_color(16, 185, 129)
    amp = float(data.get("amplitude", 0.0))
    pdf.cell(82, 10, f"{amp:.2f} m/s²", ln=1)
    pdf.set_x(110)
    pdf.set_font("helvetica", "I", 8.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(82, 5, "Measured via MediaPipe & Sensor Fusion")
    
    pdf.ln(12)

    pdf.set_xy(15, 136)
    pdf.set_text_color(11, 19, 43)
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 6, "3. Tremor Severity Classification", ln=1)
    pdf.line(15, 143, 195, 143)
    pdf.ln(3)
    
    severity = str(data.get("severityLevel", "Normal"))
    border_color, bg_color = get_severity_colors(severity)
    
    pdf.set_fill_color(*bg_color)
    pdf.set_draw_color(*border_color)
    pdf.set_line_width(1.0)
    pdf.rect(15, 146, 180, 14, 'DF')
    
    pdf.set_xy(20, 150)
    pdf.set_font("helvetica", "B", 11)
    pdf.set_text_color(*border_color)
    pdf.cell(50, 6, f"DIAGNOSTIC STATUS: {severity.upper()}")
    
    pdf.set_xy(130, 150)
    pdf.set_font("helvetica", "I", 9.5)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(60, 6, f"Protocol: {data.get('selectedTask', 'Finger Tapping')}", align="R")
    
    pdf.ln(12)
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(15, 166, 180, 24, 'F')
    
    pdf.set_xy(18, 169)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 5, "Clinical Insight & Recommendations:", ln=1)
    
    pdf.set_x(18)
    pdf.set_font("helvetica", "", 9.5)
    pdf.set_text_color(51, 65, 85)

    if severity == "Normal":
        insight = "No sign of Parkinsonian rest tremor was detected during this 60-second trial. Frequency and amplitude metrics fall within normal physiological micro-vibrations."
    elif severity == "Mild":
        insight = "Trace level vibrations detected. The dominant tremor frequency is stable outside the typical Parkinsonian range. Routine follow-up screening is suggested."
    elif severity == "Moderate":
        insight = "Moderate tremor patterns observed. Rhythm and amplitude variation show minor decrescendo, which could warrant further assessment if symptoms persist."
    else: # Severe
        insight = "High-amplitude tremor detected in the standard Parkinson's range (4-6 Hz). A professional medical consultation and clinical motor assessment (UPDRS) are highly recommended."
        
    pdf.multi_cell(174, 4.5, insight)
    
    pdf.ln(12)
    
    pdf.set_xy(15, 196)
    pdf.set_text_color(11, 19, 43)
    pdf.set_font("helvetica", "B", 13)
    pdf.cell(0, 6, "4. Sensor-Fusion & Physiology", ln=1)
    pdf.line(15, 203, 195, 203)
    pdf.ln(3)
    
    pdf.set_fill_color(248, 250, 252)
    pdf.rect(15, 205, 180, 22, 'F')

    pdf.set_xy(18, 208)
    pdf.set_font("helvetica", "B", 10)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(60, 5, "PPG Heart Rate Monitoring:")
    pdf.set_font("helvetica", "", 10)
    pdf.set_text_color(51, 65, 85)
    pdf.cell(80, 5, f"{data.get('heartRate', 72)} BPM (Beats per Minute)")
    
    pdf.ln(6)
    pdf.set_x(18)
    pdf.set_font("helvetica", "I", 9)
    pdf.set_text_color(71, 85, 105)
    pdf.cell(0, 5, "Co-analyzed in parallel with vibration readings to correlate cardiac activity with physical tremor frequency.")
    
    pdf.set_xy(15, 240)
    pdf.set_draw_color(148, 163, 184)
    pdf.set_line_width(0.5)
    
    pdf.line(15, 255, 75, 255)
    pdf.set_xy(15, 257)
    pdf.set_font("helvetica", "", 9)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(60, 5, "Clinician Signature", align="C", ln=1)
    
    pdf.line(135, 255, 195, 255)
    pdf.set_xy(135, 257)
    pdf.cell(60, 5, "Technician / Operator", align="C")
    
    os.makedirs("Reports", exist_ok=True)
    safe_name = "".join(c for c in (data.get("patientName") or "Patient") if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    safe_id = "".join(c for c in (data.get("patientID") or "ID") if c.isalnum() or c in (" ", "_", "-")).strip().replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f"Reports/Diagnostic_Report_{safe_name}_{safe_id}_{timestamp}.pdf"
    pdf.output(report_filename)
    return report_filename
