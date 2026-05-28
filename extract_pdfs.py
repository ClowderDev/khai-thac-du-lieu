import fitz
import os

pdf_dir = r"e:\Downloads\ptdlkd"
output_dir = r"e:\Downloads\ptdlkd\pdf_texts"
os.makedirs(output_dir, exist_ok=True)

pdf_files = [
    "19.Syllabus_CDIO_KhaiThacDuLieu_V4_final.pdf",
    "Bai1_TongQuan_XuanHung_New.pdf",
    "Bai1_2_TienXuLyDuLieu_Final-converted.pdf",
    "Bai2_TapPhoBienVaLuatKetHop_Final.pdf",
    "Bai3_Reduct.pdf",
    "Bai4_PhanLop_Bayes.pdf",
    "Bai5_PhanLop_CayQuyetDinh.pdf",
    "Bai6_Gomcum_new.pdf",
    "Bai7_PhanLop_Bayes.pdf",
    "Bai8_Kohonen.pdf",
    "Slide.pdf",
]

for pdf_name in pdf_files:
    pdf_path = os.path.join(pdf_dir, pdf_name)
    if not os.path.exists(pdf_path):
        print(f"SKIP: {pdf_name} not found")
        continue
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    
    out_name = pdf_name.replace(".pdf", ".txt")
    out_path = os.path.join(output_dir, out_name)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"OK: {pdf_name} -> {out_name} ({len(text)} chars)")

print("Done!")
