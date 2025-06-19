import tkinter as tk
from tkinter import ttk, messagebox

# Add item to inventory
def add_item():
    item = item_name_entry.get()
    price = price_entry.get()
    qty = quantity_entry.get()

    if not item or not price or not qty:
        messagebox.showwarning("Input Error", "All fields are required!")
        return

    try:
        price = float(price)
        qty = int(qty)
        inventory[item] = {'Price': price, 'Quantity': qty}
        update_inventory_table()
        clear_entries()
        status_label.config(text=f"Added {item} to inventory.")
    except ValueError:
        messagebox.showerror("Input Error", "Invalid price or quantity!")

# Clear input fields
def clear_entries():
    item_name_entry.delete(0, tk.END)
    price_entry.delete(0, tk.END)
    quantity_entry.delete(0, tk.END)

# Update inventory table
def update_inventory_table():
    for row in inventory_table.get_children():
        inventory_table.delete(row)
    for item, details in inventory.items():
        inventory_table.insert("", tk.END, values=(item, details['Price'], details['Quantity']))

# Add to cart
def add_to_cart():
    item = cart_item_entry.get()
    qty = cart_qty_entry.get()

    if item not in inventory:
        messagebox.showerror("Error", "Item not found in inventory!")
        return
    try:
        qty = int(qty)
        if qty > inventory[item]['Quantity']:
            messagebox.showwarning("Error", "Not enough stock!")
            return
        inventory[item]['Quantity'] -= qty
        cart[item] = cart.get(item, 0) + qty
        update_cart_table()
        update_inventory_table()
        cart_item_entry.delete(0, tk.END)
        cart_qty_entry.delete(0, tk.END)
        status_label.config(text=f"Added {qty} x {item} to cart.")
    except ValueError:
        messagebox.showerror("Input Error", "Invalid quantity!")

# Update cart table
def update_cart_table():
    for row in cart_table.get_children():
        cart_table.delete(row)
    total_cost = 0
    for item, qty in cart.items():
        price = inventory[item]['Price']
        total = price * qty
        total_cost += total
        cart_table.insert("", tk.END, values=(item, price, qty, total))
    total_label.config(text=f"Total: ${total_cost:.2f}")

# Generate bill
def generate_bill():
    if not cart:
        messagebox.showwarning("Error", "Cart is empty!")
        return

    bill_window = tk.Toplevel(root)
    bill_window.title("Bill Details")
    bill_window.geometry("450x600")
    bill_window.resizable(False, False)

    tk.Label(bill_window, text="Grocery Management System", font=("Arial", 16, "bold")).pack(pady=10)
    tk.Label(bill_window, text="Detailed Bill", font=("Arial", 14, "bold")).pack()
    tk.Label(bill_window, text="-" * 50).pack()

    bill_frame = tk.Frame(bill_window, padx=10, pady=10)
    bill_frame.pack(fill=tk.BOTH, expand=True)

    bill_text = tk.Text(bill_frame, font=("Courier New", 12), wrap="none")
    bill_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    scrollbar = ttk.Scrollbar(bill_frame, command=bill_text.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    bill_text.config(yscrollcommand=scrollbar.set)

    total_cost = 0
    bill_content = f"{'Item':<15}{'Price':<10}{'Qty':<8}{'Total':<10}\n"
    bill_content += "-" * 50 + "\n"
    for item, qty in cart.items():
        price = inventory[item]['Price']
        total = price * qty
        total_cost += total
        bill_content += f"{item:<15}${price:<10.2f}{qty:<8}${total:<10.2f}\n"
    bill_content += "-" * 50 + "\n"
    bill_content += f"{'Total':<15}{'':<10}{'':<8}${total_cost:.2f}\n"

    bill_text.insert(tk.END, bill_content)
    bill_text.config(state="disabled")

    ttk.Button(bill_window, text="Close", command=bill_window.destroy).pack(pady=10)

    cart.clear()
    update_cart_table()

# Show Welcome Page
def show_welcome_page():
    splash = tk.Toplevel()
    splash.geometry("400x300")
    splash.title("Welcome")
    splash.configure(bg="#f0f0f0")
    splash.resizable(False, False)

    # Welcome Message
    tk.Label(splash, text="Welcome to Grocery Management System", font=("Arial", 18, "bold"), bg="#f0f0f0").pack(pady=50)
    tk.Label(splash, text="Click ENTER to proceed", font=("Arial", 14), bg="#f0f0f0").pack(pady=20)

    # ENTER Button
    def go_to_main():
        splash.destroy()  # Close the welcome page
        root.deiconify()  # Show the main inventory page

    ttk.Button(splash, text="ENTER", command=go_to_main).pack(pady=20)

    # Hide the main window until the ENTER button is clicked
    root.withdraw()
# Initialize app
root = tk.Tk()
root.title("Grocery Management System")
root.geometry("1000x600")

# Global variables
inventory = {}
cart = {}

# Show welcome page before main window
root.withdraw()  # Hide main window initially
show_welcome_page()
# root.deiconify()  # Show main window after splash

# Inventory Management Section
inventory_frame = tk.LabelFrame(root, text="Inventory Management", padx=10, pady=10)
inventory_frame.pack(fill=tk.X, padx=10, pady=5)

tk.Label(inventory_frame, text="Item Name:").grid(row=0, column=0)
item_name_entry = ttk.Entry(inventory_frame, width=20)
item_name_entry.grid(row=0, column=1)

tk.Label(inventory_frame, text="Price:").grid(row=0, column=2)
price_entry = ttk.Entry(inventory_frame, width=10)
price_entry.grid(row=0, column=3)

tk.Label(inventory_frame, text="Quantity:").grid(row=0, column=4)
quantity_entry = ttk.Entry(inventory_frame, width=10)
quantity_entry.grid(row=0, column=5)

ttk.Button(inventory_frame, text="Add Item", command=add_item).grid(row=0, column=6, padx=5)
ttk.Button(inventory_frame, text="Clear", command=clear_entries).grid(row=0, column=7)

# Inventory Table
inventory_table = ttk.Treeview(root, columns=("Item", "Price", "Quantity"), show="headings", height=10)
inventory_table.pack(fill=tk.X, padx=10, pady=5)
inventory_table.heading("Item", text="Item")
inventory_table.heading("Price", text="Price")
inventory_table.heading("Quantity", text="Quantity")

# Cart Section
cart_frame = tk.LabelFrame(root, text="Shopping Cart", padx=10, pady=10)
cart_frame.pack(fill=tk.X, padx=10, pady=5)

tk.Label(cart_frame, text="Item:").grid(row=0, column=0)
cart_item_entry = ttk.Entry(cart_frame, width=20)
cart_item_entry.grid(row=0, column=1)

tk.Label(cart_frame, text="Quantity:").grid(row=0, column=2)
cart_qty_entry = ttk.Entry(cart_frame, width=10)
cart_qty_entry.grid(row=0, column=3)

ttk.Button(cart_frame, text="Add to Cart", command=add_to_cart).grid(row=0, column=4, padx=5)
ttk.Button(cart_frame, text="Generate Bill", command=generate_bill).grid(row=0, column=5)

# Cart Table
cart_table = ttk.Treeview(root, columns=("Item", "Price", "Quantity", "Total"), show="headings", height=10)
cart_table.pack(fill=tk.X, padx=10, pady=5)
cart_table.heading("Item", text="Item")
cart_table.heading("Price", text="Price")
cart_table.heading("Quantity", text="Quantity")
cart_table.heading("Total", text="Total")

# Total Label
total_label = tk.Label(root, text="Total: $0.00", font=("Arial", 14), anchor="e")
total_label.pack(fill=tk.X, padx=10, pady=5)

# Status Bar
status_bar = tk.Frame(root, bg="#f0f0f0", height=30)
status_bar.pack(fill=tk.X, side=tk.BOTTOM)
status_label = tk.Label(status_bar, text="Welcome to Grocery Management System", anchor="w")
status_label.pack(fill=tk.X, padx=10)

# Run the app
root.mainloop()
