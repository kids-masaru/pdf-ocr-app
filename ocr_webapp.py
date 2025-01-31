import os
import fitz
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
import streamlit as st

# Tesseractの設定（適宜ご自身の環境に合わせて設定してください）
# TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# TESSDATA_PATH = r"C:\Program Files\Tesseract-OCR\tessdata"
# os.environ["TESSDATA_PREFIX"] = TESSDATA_PATH
# pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH

# ファイル: ocr_webapp.py の該当部分を以下のように修正

# 修正前（コメントアウトする）
# TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
# TESSDATA_PATH = r"C:\Program Files\Tesseract-OCR\tessdata"

# 修正後（Linux用パス設定）
pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
os.environ["TESSDATA_PREFIX"] = '/usr/share/tesseract-ocr/4.00/tessdata/'


def preprocess_image(img):
    """OCR精度向上のための画像前処理"""
    cv_img = np.array(img)[:, :, ::-1].copy()
    # グレースケール変換
    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
    # 画像の平滑化（ノイズ除去）
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    # 明るさの自動調整（コントラスト強調）
    norm_img = cv2.normalize(blurred, None, alpha=0, beta=255, norm_type=cv2.NORM_MINMAX)
    # 適応的閾値処理（二値化）
    bin_img = cv2.adaptiveThreshold(norm_img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 10)
    # ノイズ除去（小さなゴミを除去）
    denoised = cv2.medianBlur(bin_img, 3)
    # コントラスト強化
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    enhanced_img = clahe.apply(denoised)
    
    return Image.fromarray(enhanced_img)

def get_ocr_config():
    """OCRの設定パラメータ"""
    return (
        "--oem 3 "
        "--psm 6 "
        "-l jpn+jpn_vert "
        "--dpi 300 "
        "-c preserve_interword_spaces=1"  # 修正: -c オプションを使用
    )
    
def process_page(page):
    """ページごとのOCR処理"""
    dpi = 300
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    img = Image.open(io.BytesIO(pix.tobytes()))
    processed_img = preprocess_image(img)
    custom_config = get_ocr_config()
    ocr_pdf = pytesseract.image_to_pdf_or_hocr(processed_img, extension='pdf', config=custom_config)
    return ocr_pdf

def process_pdf(pdf_bytes, progress_bar, status_text):
    """PDF全体のOCR処理"""
    doc = fitz.open("pdf", pdf_bytes)
    output_doc = fitz.open()
    total_pages = len(doc)

    try:
        for page_num in range(total_pages):
            status_text.text(f"処理中: {page_num + 1}/{total_pages} ページ")
            ocr_pdf = process_page(doc[page_num])
            temp_doc = fitz.open("pdf", ocr_pdf)
            output_doc.insert_pdf(temp_doc)
            temp_doc.close()
            progress_bar.progress((page_num + 1) / total_pages)

        output_doc.set_metadata(doc.metadata)
        output_bytes = io.BytesIO()
        output_doc.save(output_bytes, garbage=4, clean=True, deflate=True)
        output_doc.close()
        doc.close()

        return output_bytes.getvalue()
    except Exception as e:
        if output_doc:
            output_doc.close()
        if doc:
            doc.close()
        raise e

def main():
    # ページ設定
    st.set_page_config(
        page_title="PDF OCR Converter",
        page_icon="📄",
        layout="centered"
    )

    # ---------- カスタムCSS ----------
    st.markdown("""
        <style>
        /* 全体レイアウト調整 */
        .main {
            padding: 2rem;
        }
        /* タイトルのデザイン */
        .stTitle {
            font-size: 3rem !important;
            color: #1E88E5;
            padding-bottom: 2rem;
        }
        /* サブタイトルのデザイン */
        .subtitle {
            text-align: center;
            color: #666666;
            padding-bottom: 2rem;
            font-size: 1rem;
        }
        /* アップロードセクション */
        .upload-section {
            background-color: #f8f9fa;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 2rem;
        }
        /* ドラッグ＆ドロップエリアのスタイル */
        div[data-testid="stFileUploadDropzone"] {
            background-color: #ffffff;
            border: 2px dashed #1E88E5;
            border-radius: 8px;
            padding: 1rem;
        }
        /* ファイルの上限サイズなどの表示を非表示にする場合 */
        div[data-testid="stFileUploadInstructions"] {
            display: none !important;
        }
        /* プログレスバーなどのステータスセクション */
        .status-section {
            margin-top: 2rem;
            padding: 1.5rem;
            border-radius: 8px;
            background-color: #ffffff;
        }
        /* ダウンロードボタンをおしゃれに */
        .download-button {
            margin-top: 1.5rem;
        }
        .stButton>button {
            background-color: #1E88E5 !important;
            color: white !important;
            border-radius: 5px !important;
            padding: 0.5rem 1.5rem !important;
            border: none !important;
            font-size: 1rem;
        }
        .stButton>button:hover {
            background-color: #1976D2 !important;
            color: #ffffff !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # ---------- ヘッダー部分 ----------
    col_icon, col_title = st.columns([1, 4])
    with col_icon:
        st.markdown("# 📄")
    with col_title:
        st.title("PDF OCR Converter")

    st.markdown(
        "<div class='subtitle'>スキャンされたPDFを検索可能なデジタル文書に変換します</div>",
        unsafe_allow_html=True
    )

    # ---------- セッション状態の初期化 ----------
    if 'processed_pdf' not in st.session_state:
        st.session_state.processed_pdf = None
    if 'processing' not in st.session_state:
        st.session_state.processing = False
    if 'last_processed_file' not in st.session_state:
        st.session_state.last_processed_file = None
    if 'original_filename' not in st.session_state:
        st.session_state.original_filename = None

    # ---------- メインセクション（ファイルアップロード） ----------
    with st.container():
        st.markdown('<div class="upload-section">', unsafe_allow_html=True)
        
        # ファイルアップロードのラベル類を非表示にして、CSSでも追加説明を消す
        uploaded_file = st.file_uploader(
            label="",  # デフォルトのラベルは非表示
            type=["pdf"],
            label_visibility="collapsed",  # ラベルを折りたたむ
            help=None  # 既定のヘルプも非表示
        )
        
        # 独自の受付テキストを配置
        st.markdown("""
            <div style='text-align: center; color: #666666; margin-top: 1rem; font-size: 1rem;'>
            PDFファイルをドラッグ＆ドロップまたはクリックして選択 (最大 200MB程度)
            </div>
        """, unsafe_allow_html=True)       

        if uploaded_file:
            current_file = uploaded_file.name
            st.markdown(f"""
                <div style='text-align: center; padding: 1rem;'>
                選択されたファイル: <strong>{current_file}</strong>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- OCR処理セクション ----------
    if uploaded_file:
        # すでに処理中でない、または前回と異なるファイルの場合のみ処理
        if ((st.session_state.last_processed_file != uploaded_file.name) or 
            (st.session_state.processed_pdf is None)) and not st.session_state.processing:
            try:
                st.markdown('<div class="status-section">', unsafe_allow_html=True)
                st.session_state.processing = True
                
                # プログレスバーとステータス表示
                c1, c2 = st.columns([3, 1])
                with c1:
                    progress_bar = st.progress(0)
                with c2:
                    status_text = st.empty()

                with st.spinner("OCR処理を実行中..."):
                    st.session_state.processed_pdf = process_pdf(
                        uploaded_file.read(),
                        progress_bar,
                        status_text
                    )

                progress_bar.empty()
                status_text.markdown("✔️ 処理完了")

                st.session_state.processing = False
                st.session_state.last_processed_file = uploaded_file.name
                st.session_state.original_filename = uploaded_file.name

                st.success("PDF変換が完了しました。ダウンロードボタンをクリックしてください。")
                st.markdown('</div>', unsafe_allow_html=True)

            except Exception as e:
                st.error(f"エラーが発生しました: {str(e)}")
                st.session_state.processing = False
                st.session_state.processed_pdf = None
                st.session_state.last_processed_file = None
                st.session_state.original_filename = None

    # ---------- ダウンロードボタン ----------
    if st.session_state.processed_pdf is not None and st.session_state.original_filename:
        download_filename = f"OCR_{st.session_state.original_filename}"
        st.markdown('<div class="download-button">', unsafe_allow_html=True)
        _, download_col, _ = st.columns([1,2,1])
        with download_col:
            st.download_button(
                label="⇓ OCR処理済みPDFをダウンロード ⇓",
                data=st.session_state.processed_pdf,
                file_name=download_filename,
                mime="application/pdf",
                use_container_width=True
            )
        st.markdown('</div>', unsafe_allow_html=True)

    # ---------- フッター ----------
    st.markdown("""
        <div style='text-align: center; color: #666666; padding-top: 3rem; font-size: 0.8rem;'>
        © 2024 PDF OCR Converter | Powered by Tesseract OCR
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()