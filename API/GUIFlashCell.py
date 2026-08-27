# from GUICreateWatchListTab import table
from GUIGlobalVariables import root

def flashCell(scrip, flashColor, table):
    # Get the item ID of the cell corresponding to the given scrip
    item_id = None
    column_id = 1  # Assuming the cell to flash is in the second column (index 1)
    for item in table.get_children():
        if table.item(item, "values")[0] == scrip:
            item_id = item
            break
    # Flash the cell by changing its background color
    if item_id:
        table.tag_configure("flash", background=flashColor)
        table.item(item_id, tags=("flash",))
        root.after(1000, lambda: clearFlash(item_id, column_id, table))  

def clearFlash(item_id, column_id, table):
    # Clear the flash effect by restoring the default background color of the cell
    table.item(item_id, tags=())