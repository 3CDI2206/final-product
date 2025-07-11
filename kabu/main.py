import subprocess
import sys

# 必要ライブラリの自動インストール関数
def install_if_missing(package):
    try:
        __import__(package)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# 必要なパッケージをすべて確認＆インストール
for pkg in ["yfinance", "japanize_matplotlib", "Pillow", "matplotlib", "pytz", "googletrans==4.0.0-rc1", "requests"]:
    install_if_missing(pkg)

# import
import tkinter as tk
from tkinter import ttk, messagebox
import yfinance as yf
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import io
import os
import json
import pytz
import webbrowser
from datetime import datetime
from news_fetcher import get_company_news, translate_text
import japanize_matplotlib

JP_TZ = pytz.timezone("Asia/Tokyo")
DATA_FILE = "stock_list.json"
default_symbols = ["AAPL", "TSLA", "NVDA", "7203.T", "9984.T"]

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        stock_symbols = json.load(f)
else:
    stock_symbols = default_symbols

period_options = {
    "1日 (Today)": "1d", "1週間": "7d", "1か月": "1mo", "3か月": "3mo",
    "6か月": "6mo", "年初来": "ytd", "1年": "1y", "2年": "2y",
    "5年": "5y", "10年": "10y", "すべて": "max"
}

root = tk.Tk()
root.title("株価ビューア")
root.geometry("1100x700")
main_frame = tk.Frame(root)
main_frame.pack(fill="both", expand=True)

left_frame = tk.Frame(main_frame, width=320, bg="#f0f0f0")
left_frame.pack(side="left", fill="y")
search_frame = tk.Frame(left_frame, bg="#d0d0d0")
search_frame.pack(fill="x", padx=5, pady=5)
search_entry = tk.Entry(search_frame, font=("Arial", 12))
search_entry.pack(side="left", fill="x", expand=True, padx=5)

def save_symbols():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stock_symbols, f, ensure_ascii=False)

def resolve_symbol(user_input):
    ui = user_input.strip()
    # 数字4桁なら日本株コードとする
    if ui.isdigit() and len(ui) == 4:
        return ui + ".T"
    # 英字（米株ティッカー）ならそのまま
    if ui.isalpha():
        return ui
    # 日本語企業名、例「ソフトバンク」で検索
    try:
        search = yf.Ticker(ui).info.get("symbol")
        if search:
            return search
    except:
        pass
    return None

def add_stock():
    inp = search_entry.get().strip()
    sym = resolve_symbol(inp.upper())
    if not sym:
        messagebox.showerror("エラー", f"'{inp}' は有効な銘柄ではありません。")
        return
    if sym in stock_symbols:
        messagebox.showinfo("情報", f"すでに '{sym}' はリストにあります。")
        return
    try:
        info = yf.Ticker(sym).info
        if info.get("regularMarketPrice") is None:
            raise Exception()
        stock_symbols.append(sym)
        add_stock_card(sym)
        save_symbols()
    except:
        messagebox.showerror("エラー", f"'{sym}' の情報が取得できませんでした。")

search_button = tk.Button(search_frame, text="追加", command=add_stock)
search_button.pack(side="right", padx=5)

canvas = tk.Canvas(left_frame, bg="#f0f0f0", highlightthickness=0)
scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
scrollable_frame = tk.Frame(canvas, bg="#f0f0f0")
scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")
right_frame = tk.Frame(main_frame, bg="white")
right_frame.pack(side="right", fill="both", expand=True)

top_bar = tk.Frame(right_frame, height=50, bg="#e8e8ff")
top_bar.pack(side="top", fill="x")
info_label = tk.Label(top_bar, text="銘柄を選択してください", bg="#e8e8ff", font=("Arial", 14))
info_label.pack(side="left", padx=10, pady=10)

graph_area = tk.Frame(right_frame, bg="white")
graph_area.pack(fill="both", expand=True)

period_var = tk.StringVar()
period_var.set("1日 (Today)")
current_selected = [None]

def update_detail_graph(symbol, period_label):
    for widget in graph_area.winfo_children():
        widget.destroy()
    try:
        period_str = period_options[period_label]
        interval = "5m" if period_str == "1d" else "1d"
        ticker = yf.Ticker(symbol)
        data = ticker.history(period=period_str, interval=interval)
        if data.empty:
            raise ValueError("データが取得できませんでした。")
        data.index = data.index.tz_convert(JP_TZ)
        current = data["Close"][-1]
        base = data["Close"][0]
        change = current - base
        change_pct = (change / base) * 100
        color = "green" if change >= 0 else "red"
        label_str = f"{symbol} 現在値: {current:.2f}（{'+' if change >= 0 else ''}{change:.2f}, {change_pct:.2f}%）"
        label = tk.Label(graph_area, text=label_str, fg=color, bg="white", font=("Arial", 14, "bold"))
        label.pack()
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        ax.plot(data.index, data["Close"], color=color)
        ax.set_title(f"{symbol} の株価推移（{period_label}）")
        ax.set_xlabel("日付")
        ax.set_ylabel("価格")
        ax.grid(True)
        fig.autofmt_xdate()
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=graph_area)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
    except Exception as e:
        error = tk.Label(graph_area, text=f"取得失敗: {e}", fg="red", bg="white")
        error.pack()

def on_stock_click(symbol):
    current_selected[0] = symbol
    info_label.config(text=f"{symbol} の詳細を表示中")
    update_detail_graph(symbol, period_var.get())
    update_news_bar(symbol)

def get_mini_graph(symbol):
    try:
        hist = yf.Ticker(symbol).history(period="1d", interval="5m")
        if hist.empty: return None
        color = "green" if hist["Close"][-1] >= hist["Close"][0] else "red"
        fig, ax = plt.subplots(figsize=(2.5, 0.6), dpi=100)
        ax.plot(hist["Close"], color=color)
        ax.axis("off")
        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches='tight', pad_inches=0)
        plt.close(fig)
        buf.seek(0)
        img = Image.open(buf)
        return ImageTk.PhotoImage(img)
    except:
        return None

def create_tooltip(widget, text):
    tooltip = tk.Toplevel(widget)
    tooltip.wm_overrideredirect(True)
    tooltip.wm_geometry("0x0+0+0")
    label = tk.Label(tooltip, text=text, background="yellow", relief="solid", borderwidth=1, font=("Arial", 9))
    label.pack()
    tooltip.withdraw()

    def show_tooltip(event):
        x = event.x_root + 10
        y = event.y_root + 10
        tooltip.wm_geometry(f"+{x}+{y}")
        tooltip.deiconify()

    def hide_tooltip(event):
        tooltip.withdraw()

    widget.bind("<Enter>", show_tooltip)
    widget.bind("<Leave>", hide_tooltip)

def add_stock_card(symbol):
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        price = info.get("regularMarketPrice", 0)
        change = info.get("regularMarketChangePercent", 0)
    except:
        return

    frame = tk.Frame(scrollable_frame, bg="white", relief="solid", bd=1)
    frame.pack(fill="x", padx=5, pady=2)

    delete_button = tk.Button(frame, text="×", fg="white", bg="red", font=("Arial", 10, "bold"),
                              command=lambda s=symbol, f=frame: delete_stock(s, f))
    delete_button.pack(side="left", padx=3)
    create_tooltip(delete_button, "削除する")

    name_label = tk.Label(frame, text=symbol.replace(".T", ""), font=("Arial", 12, "bold"),
                          width=8, anchor="w", bg="white")
    change_color = "green" if change >= 0 else "red"
    change_text = f"▲ {change:.2f}%" if change >= 0 else f"▼ {abs(change):.2f}%"
    change_label = tk.Label(frame, text=change_text, fg=change_color, width=10, anchor="w", bg="white")
    price_label = tk.Label(frame, text=f"{price:.2f}", width=10, anchor="e", bg="white")

    name_label.pack(side="left", padx=5)
    change_label.pack(side="left")
    price_label.pack(side="left", padx=5)

    graph_image = get_mini_graph(symbol)
    if graph_image:
        graph_label = tk.Label(frame, image=graph_image, bg="white")
        graph_label.image = graph_image
        graph_label.pack(side="left", padx=5)

    frame.bind("<Button-1>", lambda e, sym=symbol: on_stock_click(sym))
    for widget in frame.winfo_children():
        if widget != delete_button:
            widget.bind("<Button-1>", lambda e, sym=symbol: on_stock_click(sym))

def delete_stock(symbol, frame):
    if messagebox.askyesno("確認", f"{symbol} を本当に削除しますか？"):
        try:
            stock_symbols.remove(symbol)
            save_symbols()
            frame.destroy()
        except Exception as e:
            print(f"[削除エラー] {symbol}: {e}")

period_menu = ttk.Combobox(top_bar, values=list(period_options.keys()), textvariable=period_var, state="readonly", width=15)
period_menu.pack(side="right", padx=10)
period_menu.bind("<<ComboboxSelected>>", lambda e: update_detail_graph(current_selected[0], period_var.get()))

news_frame = tk.Frame(root, height=40, bg="#eeeeee")
news_frame.pack(side="bottom", fill="x")

news_canvas = tk.Canvas(news_frame, height=40, bg="#eeeeee", highlightthickness=0)
news_canvas.pack(side="left", fill="both", expand=True)

news_inner = tk.Frame(news_canvas, bg="#eeeeee")
news_window = news_canvas.create_window((0, 0), window=news_inner, anchor="nw", tags="scroll_text")

def update_news_bar(company_name):
    for widget in news_inner.winfo_children():
        widget.destroy()
    articles = get_company_news(company_name)
    for title, url in articles:
        try:
            jp_title = translate_text(title)
        except:
            jp_title = title
        if not jp_title:
            jp_title = title
        label = tk.Label(news_inner, text=jp_title, fg="blue", bg="#eeeeee", font=("Arial", 12, "bold"),
                         cursor="hand2", padx=30)
        label.pack(side="left")
        label.bind("<Button-1>", lambda e, link=url: webbrowser.open(link))
    news_inner.update_idletasks()
    news_canvas.config(scrollregion=news_canvas.bbox("all"))

def scroll_news():
    news_canvas.move("scroll_text", -2, 0)
    if news_canvas.bbox("scroll_text") and news_canvas.bbox("scroll_text")[2] < 0:
        news_canvas.move("scroll_text", news_canvas.winfo_width(), 0)
    news_canvas.after(50, scroll_news)

scroll_news()

for s in stock_symbols:
    add_stock_card(s)
current_selected[0] = stock_symbols[0]
on_stock_click(stock_symbols[0])

root.mainloop()
