from GUIGlobalVariables import notebook
from GUIGlobalVariables import root
from GUIGlobalVariables import staleEquityVsLTP
import pandas as pd
from tkinter import ttk
import tkinter as tk
import prepareFinalHoldings
from GUIStreamLTP import streamStaleLTP

excel_file = '/Users/bhavya/Downloads/HOLDINGS/PAPA.xlsx'
dataframe = pd.read_excel(excel_file, 0)

def createFinalHoldingsTab(finalHoldings):
    tabFrame = ttk.Frame(notebook)
    notebook.add(tabFrame, text="Final Holdings")
    # label = tk.Label(tab_frame, text=f"This is Tab {notebook.index('end')}")
    # label.pack(side=tk.LEFT)  # Pack the label to the left of the tab text
    if notebook.index('end') != 0:  # Check if the tab index is not 0 (i.e., not the first tab)
        close_canvas = tk.Canvas(tabFrame, width=15, height=15, bg='white', highlightthickness=0)
        close_canvas.pack(side=tk.RIGHT, anchor=tk.NE, padx=5, pady=5)
        close_canvas.create_oval(2, 2, 13, 13, fill='red')
        close_canvas.bind('<Button-1>', lambda event: close_tab(tabFrame))
        # close_button = tk.Button(tab_frame, text="✕", command=lambda: close_tab(tab_frame), bd=0, bg="white", fg="red", font=("Arial", 8, "bold"))
        # close_button.pack(side=tk.RIGHT, anchor=tk.NE)  # Pack the close button to the top-right corner without padding
    allColumnsInFinalHoldings(tabFrame, finalHoldings)
    notebook.select(tabFrame)

def allColumnsInFinalHoldings(tabFrame, finalHoldings):
    # def open_new_tab(scrip):
    #     # Implement the logic to open a new tab based on the selected scrip
    #     # For example:
    #     tab_frame = ttk.Frame(notebook)
    #     notebook.add(tab_frame, text=scrip)
    #     notebook.select(tabFrame)

    #     # Add content to the new tab as needed

    # def on_double_click(event):
    #     item = table.selection()[0]  # Get the selected item
    #     scrip = table.item(item, "values")[0]  # Get the value of the first column (assuming it's the scrip)
    #     print (item, scrip)   
    #     open_new_tab(scrip)
     
        # Create a dictionary to store the current sorting order for each column
    sort_order = {"EQUITY": "asc", "QUANTITY": "asc", "AVERAGE BUY": "asc", "TOTAL BUY": "asc", "LTP": "asc", "TOTAL VALUE": "asc", "UNREALISED P/L": "asc", "P/L %": "asc"}
    # Create a list to store the data displayed in the Treeview
    table_data = []

    table = ttk.Treeview(tabFrame)
    # style = ttk.Style()
    # style.configure("Treeview.Heading", background="red", foreground="white", font=("Arial", 15, "bold"))
    # style = ttk.Style(root)
    # style.theme_use("clam")
    # style.configure("Treeview.Heading", background="black", foreground="lightgray", fieldbackground="red")

    table["columns"] = ("EQUITY", "QUANTITY", "AVERAGE BUY", "TOTAL BUY", "LTP", "TOTAL VALUE", "UNREALISED P/L", "P/L %")
    table.column("#0", width=0, stretch=tk.NO)  # Hide the default column
    table.column("EQUITY", anchor=tk.CENTER, width=100)
    table.column("QUANTITY", anchor=tk.CENTER, width=50)
    table.column("AVERAGE BUY", anchor=tk.CENTER, width=50)  
    table.column("TOTAL BUY", anchor=tk.CENTER, width=50)  
    table.column("LTP", anchor=tk.CENTER, width=50)  
    table.column("TOTAL VALUE", anchor=tk.CENTER, width=50)  
    table.column("UNREALISED P/L", anchor=tk.CENTER, width=50)  
    table.column("P/L %", anchor=tk.CENTER, width=50)  
    table.heading("EQUITY", text="EQUITY", command=lambda: sortTableColumn(table, "EQUITY", sort_order, table_data))
    table.heading("QUANTITY", text="QUANTITY", command=lambda: sortTableColumn(table, "QUANTITY", sort_order, table_data))
    table.heading("AVERAGE BUY", text="AVERAGE BUY", command=lambda: sortTableColumn(table, "AVERAGE BUY", sort_order, table_data))
    table.heading("TOTAL BUY", text="TOTAL BUY", command=lambda: sortTableColumn(table, "TOTAL BUY", sort_order, table_data))
    table.heading("LTP", text="LTP", command=lambda: sortTableColumn(table, "LTP", sort_order, table_data))
    table.heading("TOTAL VALUE", text="TOTAL VALUE", command=lambda: sortTableColumn(table, "TOTAL VALUE", sort_order, table_data))
    table.heading("UNREALISED P/L", text="UNREALISED P/L", command=lambda: sortTableColumn(table, "UNREALISED P/L", sort_order, table_data))
    table.heading("P/L %", text="P/L %", command=lambda: sortTableColumn(table, "P/L %", sort_order, table_data))
    
    for equity, data in finalHoldings.items():
        averageBuy = round(data[0], 3)
        qty = round(data[1], 3)
        totalBuy = round(averageBuy * qty, 3)
        ltp = round(staleEquityVsLTP[equity], 3)
        totalValue = round(ltp * qty, 3)
        unrealisedPnl = round((ltp - averageBuy) * qty, 3)
        pnlPercentage = round(100 * unrealisedPnl/ (qty * averageBuy), 3)
        table_data.append((equity, qty, averageBuy, totalBuy, ltp, totalValue, unrealisedPnl, pnlPercentage))
        displayTableData(table, table_data)
        # table.insert("", "end", values=(equity, qty, averageBuy, totalBuy, ltp, totalValue, unrealisedPnl, pnlPercentage))
    table.pack(fill="both", expand=True)
    # table.bind("<Double-1>", on_double_click)

    # notebook.select(tabFrame)


def close_tab(tab_frame):
    notebook.forget(tab_frame)

def sortTableColumn(table, column, sort_order, table_data):
    sort_order[column] = "asc" if sort_order[column] == "desc" else "desc"
    sorted_data = sorted(table_data, key=lambda x: x[table["columns"].index(column)], reverse=(sort_order[column] == "desc"))
    displayTableData(table, sorted_data)

def displayTableData(table, data):
    table.delete(*table.get_children())
    for row in data:
        table.insert("", "end", values=row)
    table.pack(fill="both", expand=True)

def GUIShowFinalHoldings():
    finalHoldings = prepareFinalHoldings.prepareFinalHoldingsMap(dataframe)
    for equity, _ in finalHoldings.items():
        if equity not in staleEquityVsLTP:
            staleEquityVsLTP[equity] = streamStaleLTP(equity)
    createFinalHoldingsTab(finalHoldings)

