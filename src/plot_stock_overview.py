"""
Vẽ biểu đồ đường so sánh xu hướng giá đóng cửa của FPT, VNM và HPG.

Cài thư viện nếu chưa có:
    pip install pandas matplotlib sqlalchemy "psycopg[binary]" python-dotenv

Chạy từ thư mục gốc project:
    python src/plot_stock_overview.py

Script đọc dữ liệu từ PostgreSQL database `stock_market`, bảng `stock_prices`.
Biểu đồ chuẩn hóa giá đóng cửa về mốc 100 tại ngày đầu tiên để so sánh xu hướng
giữa các mã có mức giá khác nhau.
"""

import os
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


# Đọc cấu hình từ file .env ở thư mục gốc project.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

SYMBOLS = ["FPT", "VNM", "HPG"]
OUTPUT_DIR = PROJECT_ROOT / "reports"
OUTPUT_FILE = OUTPUT_DIR / "stock_overview.png"


def create_db_engine():
    """Tạo kết nối PostgreSQL từ DATABASE_URL hoặc các biến DB_* trong .env."""
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return create_engine(database_url)

    required = ["DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [key for key in required if os.getenv(key) is None]
    if missing:
        raise RuntimeError(
            "Thiếu cấu hình database trong .env: "
            + ", ".join(missing)
            + ". Hãy khai báo DATABASE_URL hoặc DB_NAME, DB_USER, DB_PASSWORD."
        )

    url = URL.create(
        drivername="postgresql+psycopg",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "stock_market"),
    )
    return create_engine(url, pool_pre_ping=True)


def fetch_stock_prices(engine) -> pd.DataFrame:
    """Lấy giá đóng cửa theo ngày cho ba mã từ PostgreSQL."""
    query = text(
        """
        SELECT symbol, trading_date, close
        FROM stock_prices
        WHERE symbol IN (:symbol_1, :symbol_2, :symbol_3)
        ORDER BY trading_date, symbol
        """
    )

    with engine.connect() as connection:
        df = pd.read_sql_query(
            query,
            connection,
            params={
                "symbol_1": SYMBOLS[0],
                "symbol_2": SYMBOLS[1],
                "symbol_3": SYMBOLS[2],
            },
        )

    if df.empty:
        raise RuntimeError(
            "Không tìm thấy dữ liệu. Hãy kiểm tra database stock_market "
            "và bảng stock_prices."
        )

    df["trading_date"] = pd.to_datetime(df["trading_date"])
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    df = df.dropna(subset=["trading_date", "close"])
    return df


def plot_overview(df: pd.DataFrame) -> None:
    """Vẽ đường chỉ số giá chuẩn hóa, mốc 100 là giá đóng cửa đầu tiên của mỗi mã."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pivot = df.pivot_table(
        index="trading_date",
        columns="symbol",
        values="close",
        aggfunc="last",
    ).sort_index()

    available_symbols = [symbol for symbol in SYMBOLS if symbol in pivot.columns]
    missing_symbols = [symbol for symbol in SYMBOLS if symbol not in pivot.columns]
    if missing_symbols:
        print(f"[WARNING] Không có dữ liệu cho: {', '.join(missing_symbols)}")

    if not available_symbols:
        raise RuntimeError("Không có mã cổ phiếu hợp lệ để vẽ biểu đồ.")

    # Chuẩn hóa từng mã về 100 tại phiên đầu tiên có dữ liệu của mã đó.
    normalized = pd.DataFrame(index=pivot.index)
    for symbol in available_symbols:
        series = pivot[symbol].dropna()
        if series.empty or series.iloc[0] == 0:
            print(f"[WARNING] Bỏ qua {symbol}: không có giá hợp lệ để chuẩn hóa.")
            continue
        normalized[symbol] = pivot[symbol] / series.iloc[0] * 100

    if normalized.empty:
        raise RuntimeError("Không có dữ liệu hợp lệ sau khi chuẩn hóa.")

    fig, ax = plt.subplots(figsize=(13, 6.5))

    for symbol in normalized.columns:
        ax.plot(
            normalized.index,
            normalized[symbol],
            label=symbol,
            linewidth=1.8,
        )

    ax.axhline(100, linestyle="--", linewidth=1, alpha=0.6)
    ax.set_title("Vietnam Stock Market — FPT, VNM, HPG", fontsize=15, pad=14)
    ax.set_xlabel("Ngày giao dịch")
    ax.set_ylabel("Chỉ số giá đóng cửa (phiên đầu tiên = 100)")
    ax.grid(True, linestyle="--", alpha=0.3)
    ax.legend(title="Mã cổ phiếu")
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    fig.autofmt_xdate()
    fig.tight_layout()

    fig.savefig(OUTPUT_FILE, dpi=160, bbox_inches="tight")
    print(f"[OK] Đã lưu biểu đồ tại: {OUTPUT_FILE}")
    plt.show()


def main():
    engine = create_db_engine()
    try:
        df = fetch_stock_prices(engine)
        print(f"Số dòng lấy từ database: {len(df)}")
        print(
            "Khoảng thời gian: "
            f"{df['trading_date'].min().date()} đến "
            f"{df['trading_date'].max().date()}"
        )
        plot_overview(df)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
