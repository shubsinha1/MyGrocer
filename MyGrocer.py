import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import mysql.connector
from tkinter.simpledialog import askinteger

# Function to connect to MySQL database
def connect_db():
    conn = mysql.connector.connect(
        host="localhost",         # Change to your MySQL host if needed
        user="root",              # MySQL username
        password="shub12345", # MySQL password
        database="grocery_store"  # Database name
    )
    return conn

# Function to create bills table if not exists
def create_bills_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS bills (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        item_name VARCHAR(255) NOT NULL,
                        quantity INT NOT NULL,
                        price DECIMAL(10, 2) NOT NULL,
                        total_price DECIMAL(10, 2) NOT NULL,
                        bill_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

# Function to insert bill data into the bills table
def insert_bill_data(SELECT_ITEM, QUANTITY, PRICE, TOTAL_PRICE):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bills (item_name, quantity, price, total_price) VALUES (%s, %s, %s, %s)",
                   (SELECT_ITEM, QUANTITY, PRICE, TOTAL_PRICE))
    conn.commit()
    conn.close()

# Function to open the "Generate Bill" window
def open_generate_bill_window():
    bill_window = tk.Toplevel(root)
    bill_window.title("Generate Bill")
    
    # Get screen dimensions for full-screen window
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    bill_window.geometry(f"{screen_width}x{screen_height}")

    # Background color for aesthetic
    bill_window.configure(bg="#f8f8f8")

    # Title Label
    title_label = tk.Label(
        bill_window, text="Grocery Billing System", font=("Al", 30, "bold"), bg="#f8f8f8", fg="#333"
    )
    title_label.pack(pady=20)

    # Frame for the grocery input interface
    interface_frame = tk.Frame(bill_window, bg="#fefefe", relief="groove", bd=2)
    interface_frame.pack(pady=20, padx=20, fill="both", expand=True)

    # Labels for item name, quantity, and price
    tk.Label(interface_frame, text="SELECT ITEM", font=("Helvetica", 16), bg="#fefefe").grid(row=0, column=0, padx=10, pady=10)
    tk.Label(interface_frame, text="Quantity(Kg/Unit)", font=("Helvetica", 16), bg="#fefefe").grid(row=0, column=1, padx=10, pady=10)
    tk.Label(interface_frame, text="Price (per Kg/Unit)", font=("Helvetica", 16), bg="#fefefe").grid(row=0, column=2, padx=10, pady=10)

    # Fetch inventory data for dropdown
    inventory_data = fetch_inventory_data()
    inventory_names = [item['product_name'] for item in inventory_data]

    # Replace item_name_entry with a Combobox
    item_name_var = tk.StringVar()
    item_name_combobox = ttk.Combobox(interface_frame, textvariable=item_name_var, values=inventory_names, font=("Helvetica", 14), width=18, state="readonly")
    item_name_combobox.grid(row=1, column=0, padx=10, pady=10)

    # Add spinbox for quantity
    quantity_var = tk.StringVar(value="1")
    quantity_spinbox = ttk.Spinbox(
        interface_frame,
        from_=1,
        to=999,
        textvariable=quantity_var,
        width=8,
        font=("Helvetica", 14)
    )
    quantity_spinbox.grid(row=1, column=1, padx=10, pady=10)

    # Price entry remains the same (auto-filled)
    price_entry = tk.Entry(interface_frame, font=("Helvetica", 14), borderwidth=5, width=10)
    price_entry.grid(row=1, column=2, padx=10, pady=10)

    # When an item is selected, auto-fill the price_entry
    def on_item_selected(event):
        selected_item = item_name_var.get()
        for item in inventory_data:
            if item['product_name'] == selected_item:
                price_entry.delete(0, tk.END)
                price_entry.insert(0, str(item['price']))
                break
    item_name_combobox.bind("<<ComboboxSelected>>", on_item_selected)

    # Add to cart button
    def add_to_cart():
        item = item_name_var.get()
        quantity = quantity_var.get()
        price = price_entry.get()

        if item and quantity and price:
            try:
                quantity = int(quantity)
                price = float(price)
                total_price = quantity * price
                cart.insert("", "end", values=(item, quantity, price, total_price))
                item_name_combobox.set("")
                quantity_var.set("1")  # Reset quantity to 1
                price_entry.delete(0, tk.END)
            except ValueError:
                print("Invalid quantity or price entered.")

    add_to_cart_button = tk.Button(interface_frame, text="Add to Cart", font=("Helvetica", 14), command=add_to_cart)
    add_to_cart_button.grid(row=1, column=3, padx=10, pady=10)
    
    #close_button=tk.Button(interface_frame,text="Close",font=("Lobster",20),command=interface_frame.destroy())
    #close_button.pack(pady=15, side="bottom")
    
    # Cart display
    cart_label = tk.Label(interface_frame, text="Cart", font=("Algerian", 30, "bold"), bg="#fefefe")
    cart_label.grid(row=2, column=0, columnspan=4, pady=10)

    # Treeview for displaying cart items
    cart = ttk.Treeview(interface_frame, columns=("Item", "Quantity(Unit/Kg)", "Price", "Total"), show="headings", height=15)
    cart.heading("Item", text="Item")
    cart.heading("Quantity(Unit/Kg)", text="Quantity(Unit/Kg)")
    cart.heading("Price", text="Price (per Unit/Kg)")
    cart.heading("Total", text="Total Price")
     # Configure column widths and alignment
    cart.column("Item", width=250, anchor="w")
    cart.column("Quantity(Unit/Kg)", width=200, anchor="center")
    cart.column("Price", width=200, anchor="e")
    cart.column("Total", width=200, anchor="e")
    cart.grid(row=3, column=0, columnspan=4, padx=10, pady=10)

    # Label to display the total sum
    

    # Generate Bill button
    def generate_bill():
        total_sum = 0
        for item in cart.get_children():
            total_sum += float(cart.item(item, "values")[3])  # Sum up the "Total Price" column
        title_label.config(text=f"Total: ₹{total_sum:.2f}")

        generate_bill_button = tk.Button(
        bill_window, text="Generate Bill", font=("Helvetica", 16), bg="#4CAF50", fg="white", command=generate_bill
    )
        generate_bill_button.pack(pady=10, side="bottom")

    # --- Create Bill Button ---
    def create_bill():
        # Create a new window for the bill
        bill_display_window = tk.Toplevel(bill_window)
        bill_display_window.title("Your Bill")
        bill_display_window.geometry("600x700")
        bill_display_window.configure(bg="#ffffff")

        # Title for the bill
        bill_title = tk.Label(
            bill_display_window, text="Your Grocery Bill", font=("Helvetica", 24, "bold"), bg="#ffffff", fg="#333"
        )
        bill_title.pack(pady=10)

        # Bill frame
        bill_frame = tk.Frame(bill_display_window, bg="#ffffff")
        bill_frame.pack(padx=20, pady=20, fill="both", expand=True)

        # Display items in the bill
        tk.Label(bill_frame, text="Item", font=("Helvetica", 16, "bold"), bg="#ffffff").grid(row=0, column=0, padx=10, pady=5)
        tk.Label(bill_frame, text="Quantity", font=("Helvetica", 16, "bold"), bg="#ffffff").grid(row=0, column=1, padx=10, pady=5)
        tk.Label(bill_frame, text="Price per Unit", font=("Helvetica", 16, "bold"), bg="#ffffff").grid(row=0, column=2, padx=10, pady=5)
        tk.Label(bill_frame, text="Total Price", font=("Helvetica", 16, "bold"), bg="#ffffff").grid(row=0, column=3, padx=10, pady=5)

        # Add cart items to the bill
        total_sum = 0
        bill_lines = []
        for index, item in enumerate(cart.get_children()):
            values = cart.item(item, "values")
            tk.Label(bill_frame, text=values[0], font=("Helvetica", 14), bg="#ffffff").grid(row=index + 1, column=0, padx=10, pady=5)
            tk.Label(bill_frame, text=values[1], font=("Helvetica", 14), bg="#ffffff").grid(row=index + 1, column=1, padx=10, pady=5)
            tk.Label(bill_frame, text=f"₹{values[2]}", font=("Helvetica", 14), bg="#ffffff").grid(row=index + 1, column=2, padx=10, pady=5)
            tk.Label(bill_frame, text=f"₹{values[3]}", font=("Helvetica", 14), bg="#ffffff").grid(row=index + 1, column=3, padx=10, pady=5)
            total_sum += float(values[3])
            bill_lines.append(f"{values[0]}\t{values[1]}\t₹{values[2]}\t₹{values[3]}")

        # Display the total sum
        tk.Label(bill_display_window, text=f"Grand Total: ₹{total_sum:.2f}", font=("Helvetica", 18, "bold"), bg="#ffffff", fg="#333").pack(pady=10)

        # Print Bill function
        def print_bill():
            import tkinter.filedialog as fd
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas as pdf_canvas
            from reportlab.lib import colors
            
            file_path = fd.asksaveasfilename(defaultextension=".pdf", filetypes=[("PDF files", "*.pdf")], title="Save Bill As PDF")
            if file_path:
                c = pdf_canvas.Canvas(file_path, pagesize=letter)
                width, height = letter

                # Add header with light blue background
                c.setFillColor(colors.lightblue)
                c.rect(0, height-120, width, 120, fill=True)
                
                # Add store name
                c.setFillColor(colors.darkblue)
                c.setFont("Helvetica-Bold", 36)
                c.drawString(50, height-50, "MyGrocer")
                
                # Add decorative line
                c.setStrokeColor(colors.darkblue)
                c.setLineWidth(2)
                c.line(50, height-60, width-50, height-60)
                
                # Add bill title and date
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 24)
                c.drawString(50, height-100, "INVOICE")
                
                from datetime import datetime
                current_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                c.setFont("Helvetica", 12)
                c.drawString(width-200, height-100, f"Date: {current_date}")

                # Calculate text field height based on number of items (minimum 400)
                items_count = len(bill_lines)
                field_height = max(400, items_count * 25 + 150)  # Increased padding
                
                # Define column positions
                item_x = 70
                qty_x = 250
                price_x = 380
                total_x = 480

                # Calculate vertical positions for better centering
                total_page_height = height  # total height of the page
                header_height = 120  # height of the blue header
                footer_height = 150  # approximate height needed for footer
                available_height = total_page_height - header_height - footer_height
                
                # Position the field in the center of available space
                field_start_y = height - header_height - 50 - ((available_height - field_height) / 2)

                # Draw text field background
                c.setFillColor(colors.lightgrey)
                c.rect(50, field_start_y-field_height, width-100, field_height, fill=True)
                
                # Add field border
                c.setStrokeColor(colors.grey)
                c.setLineWidth(1)
                c.rect(50, field_start_y-field_height, width-100, field_height, stroke=True)

                # Add headers (adjusted position)
                y = field_start_y - 40
                c.setFillColor(colors.black)
                c.setFont("Helvetica-Bold", 14)
                c.drawString(item_x, y, "Item")
                c.drawString(qty_x, y, "Quantity")
                c.drawString(price_x, y, "Price")
                c.drawString(total_x, y, "Total")
                
                # Add separator line
                y -= 10
                c.line(70, y, width-70, y)
                
                # Add items
                y -= 25
                c.setFont("Helvetica", 12)
                for line in bill_lines:
                    parts = line.split("\t")
                    if len(parts) == 4:
                        # Clean and format the data
                        item = parts[0].strip()
                        qty = parts[1].strip()
                        # Remove any existing currency symbols and clean the data
                        price = parts[2].replace('₹', '').replace('', '').strip()
                        total = parts[3].replace('₹', '').replace('', '').strip()
                        
                        # Draw each column with proper alignment
                        c.drawString(item_x, y, item)  # Left align item name
                        c.drawRightString(qty_x + 80, y, qty)  # Right align quantity
                        
                        # Add price with rupee symbol
                        price_text = f"₹ {price}"
                        c.drawRightString(price_x + 80, y, price_text)
                        
                        # Add total with rupee symbol
                        total_text = f"₹ {total}"
                        c.drawRightString(total_x + 60, y, total_text)
                        
                        y -= 25

                # Add separator line before total
                y -= 10
                c.setStrokeColor(colors.black)
                c.line(70, y, width-70, y)
                
                # Add total with proper alignment and rupee symbol
                y -= 30
                c.setFont("Helvetica-Bold", 14)
                c.drawString(item_x, y, "Grand Total:")
                grand_total_text = f"₹ {total_sum:.2f}"
                c.drawRightString(total_x + 60, y, grand_total_text)

                # Add footer (adjusted position)
                y = 100
                c.setFillColor(colors.grey)
                c.setFont("Helvetica", 12)
                c.drawString(50, y, "Thanks for Visiting!")
                y -= 20
                c.drawString(50, y, "Store Address: Diwan Mohalla, Sarvoday Colony")
                y -= 20
                c.drawString(50, y, "MyGrocer")
                y -= 20
                c.drawString(50, y, "Patna, Bihar")
                
                
                
                c.save()

        # Print Bill button
        print_button = tk.Button(
            bill_display_window, text="Print Bill", font=("Helvetica", 14), bg="#2196F3", fg="white", command=print_bill
        )
        print_button.pack(pady=10)

        # Close button
        close_button = tk.Button(
            bill_display_window, text="Close", font=("Helvetica", 14), bg="#f44336", fg="white", command=bill_display_window.destroy
        )
        close_button.pack(pady=10)

    # Create Bill button directly below the cart
    create_bill_button = tk.Button(interface_frame, text="Create Bill", font=("Helvetica", 16), bg="#4CAF50", fg="white", command=create_bill)
    create_bill_button.grid(row=4, column=0, columnspan=4, pady=10)


# Function to open the options window
def open_new_window():
    
    new_window = tk.Toplevel(root)
    new_window.title("Options")
    
    # Get the screen size
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    new_window.geometry(f"{screen_width}x{screen_height}")

    # Open the background image and resize it to fit the screen
    background_image = Image.open(r"C:/GMS/latest groc/grocery_store.jpg")
    background_image = background_image.resize((screen_width, screen_height))
    
    # Convert image for Tkinter compatibility
    background_image_tk = ImageTk.PhotoImage(background_image)

    # Create a canvas and add the background image
    canvas = tk.Canvas(new_window, width=screen_width, height=screen_height)
    canvas.pack(fill="both", expand=True)
    
    # Display the image on the canvas
    canvas.create_image(0, 0, image=background_image_tk, anchor="nw")
    
    # Store the image object to prevent it from being garbage collected
    canvas.image = background_image_tk

    # Button to generate bill
    generate_bill_button = tk.Button(new_window, text="GENERATE BILL", font=("Lobster", 30), bg="#4CAF50", fg="white", width=30,borderwidth=10, command=open_generate_bill_window)
    canvas.create_window(screen_width // 2, 300, window=generate_bill_button)

    # Button to open inventory window
    inventory_button = tk.Button(new_window, text="OPEN INVENTORY", font=("Helvetica", 30), bg="#4CAF50", fg="white", width=30,borderwidth=10, command=open_inventory_window)
    canvas.create_window(screen_width // 2, 450, window=inventory_button)

    # Add Item button
    add_button = tk.Button(new_window, text="ADD NEW ITEM TO INVENTORY", font=("Helvetica", 30), bg="#4CAF50", fg="white", width=30,borderwidth=10, command=add_items_to_stock_window)
    canvas.create_window(screen_width // 2, 600, window=add_button)


# Function to create inventory table if not exists
def create_inventory_table():
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS inventory (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        product_name VARCHAR(255) NOT NULL,
                        stock INT NOT NULL,
                        price DECIMAL(10, 2) NOT NULL DEFAULT 0)''')
    conn.commit()
    conn.close()

# Function to fetch inventory data from the database
def fetch_inventory_data():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)  # This ensures rows are returned as dictionaries
    cursor.execute("SELECT * FROM inventory ORDER BY stock ASC")  # Sorted by stock in ascending order
    inventory_data = cursor.fetchall()  # Fetch all rows
    conn.close()
    return inventory_data  # Return the fetched inventory data



# Function to refill stock in the database
def refill_stock_in_db(product_name, quantity):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE inventory SET stock = stock + %s WHERE product_name = %s", (quantity, product_name))
    conn.commit()
    conn.close()

# Function to open inventory window
def open_inventory_window():
    global inventory_data
    inventory_data = fetch_inventory_data()  # Fetch inventory data from MySQL
    
    # Create the inventory window
    inventory_window = tk.Toplevel(root)
    inventory_window.title("Inventory")
    inventory_window.geometry("800x600")
    inventory_window.configure(bg="#f0f8ff")  # Light blue background for aesthetics

    # Title label
    title_label = tk.Label(
        inventory_window,
        text="Inventory Overview",
        font=("Helvetica", 24, "bold"),
        bg="#f0f8ff",
        fg="#333333",
    )
    title_label.pack(pady=20)

    # Frame for table and buttons
    table_frame = tk.Frame(inventory_window, bg="#ffffff")
    table_frame.pack(pady=20, padx=30, fill="both", expand=True)

    # Scrollable canvas for table
    canvas = tk.Canvas(table_frame, bg="#ffffff")
    scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)

    scrollable_frame = tk.Frame(canvas, bg="#ffffff")
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    scrollable_frame.bind(
        "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
 # Add column headings
    heading_font = ("Helvetica", 16, "bold")
    tk.Label(scrollable_frame, text="Product", font=heading_font, bg="#ffffff").grid(row=0, column=0, padx=10, pady=10)
    tk.Label(scrollable_frame, text="Stock Available", font=heading_font, bg="#ffffff").grid(row=0, column=1, padx=10, pady=10)
    tk.Label(scrollable_frame, text="Price", font=heading_font, bg="#ffffff").grid(row=0, column=2, padx=10, pady=10)
    tk.Label(scrollable_frame, text="Action", font=heading_font, bg="#ffffff").grid(row=0, column=3, padx=10, pady=10)

     # Function to refill stock
    def refill_stock(product_name, label):
        quantity = askinteger("Refill Stock", f"Enter quantity to add for {product_name}:", minvalue=1)
        if quantity is not None:
            for item in inventory_data:
                if item["product_name"] == product_name:
                    item["stock"] += quantity
                    label.config(text=str(item["stock"]))
                    break
            # Also update the database
            current_price = next((item["price"] for item in inventory_data if item["product_name"] == product_name), 0)
            add_items_to_stock(product_name, quantity, current_price)


    # Populate table with product data and refill buttons
    for idx, item in enumerate(inventory_data, start=1):
        product = item["product_name"]
        stock = item["stock"]
        price = item["price"]
        # Product column
        tk.Label(scrollable_frame, text=product, font=("Helvetica", 14), bg="#ffffff").grid(row=idx, column=0, padx=10, pady=10)
        # Stock column
        stock_label = tk.Label(scrollable_frame, text=stock, font=("Helvetica", 14), bg="#ffffff")
        stock_label.grid(row=idx, column=1, padx=10, pady=10)
        # Price column
        tk.Label(scrollable_frame, text=f"₹{price:.2f}", font=("Helvetica", 14), bg="#ffffff").grid(row=idx, column=2, padx=10, pady=10)
        # Refill button
        refill_button = tk.Button(
            scrollable_frame,
            text="Refill",
            font=("Helvetica", 12),
            bg="#4CAF50",
            fg="white",
            command=lambda p=product, lbl=stock_label: refill_stock(p, lbl),
        )
        refill_button.grid(row=idx, column=3, padx=10, pady=10)

    # Close button
    close_button = tk.Button(
        inventory_window,
        text="Close",
        font=("Helvetica", 16),
        bg="#f44336",
        fg="white",
        command=inventory_window.destroy,
    )
    close_button.pack(pady=10)


def add_items_to_stock(item_name, quantity, price):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM inventory WHERE product_name = %s", (item_name,))
    existing_item = cursor.fetchone()
    if existing_item:
        cursor.execute("UPDATE inventory SET stock = stock + %s, price = %s WHERE product_name = %s", (quantity, price, item_name))
    else:
        cursor.execute("INSERT INTO inventory (product_name, stock, price) VALUES (%s, %s, %s)", (item_name, quantity, price))
    conn.commit()
    conn.close()
    global inventory_data
    inventory_data = fetch_inventory_data()

# Function to open the window for adding items to stock
def add_items_to_stock_window():
    global inventory_data
    add_window = tk.Toplevel(root)
    add_window.title("Add Items to Stock")
    add_window.geometry("400x400")
    add_window.configure(bg="#f0f8ff")

    tk.Label(add_window, text="Add New Item to Stock", font=("Helvetica", 18, "bold"), bg="#f0f8ff").pack(pady=20)

    # Input fields for item name, quantity, and price
    tk.Label(add_window, text="Item Name:", font=("Helvetica", 14), bg="#f0f8ff").pack(pady=5)
    item_name_entry = tk.Entry(add_window, font=("Helvetica", 12))
    item_name_entry.pack(pady=5)

    tk.Label(add_window, text="Quantity:", font=("Helvetica", 14), bg="#f0f8ff").pack(pady=5)
    quantity_entry = tk.Entry(add_window, font=("Helvetica", 12))
    quantity_entry.pack(pady=5)

    tk.Label(add_window, text="Price per Unit:", font=("Helvetica", 14), bg="#f0f8ff").pack(pady=5)
    price_entry = tk.Entry(add_window, font=("Helvetica", 12))
    price_entry.pack(pady=5)

    # Function to add the item to the inventory
    def add_item():
        global inventory_data
        item_name = item_name_entry.get()
        quantity = quantity_entry.get()
        price = price_entry.get()
        if item_name and quantity and price:
            try:
                quantity = int(quantity)
                price = float(price)
                add_items_to_stock(item_name, quantity, price)  # Update database
                # No need to append to inventory_data here, as it is refreshed from DB
                tk.Label(
                    add_window,
                    text=f"Added: {item_name} (Quantity: {quantity}, Price: ₹{price:.2f})",
                    font=("Helvetica", 12),
                    bg="#f0f8ff",
                ).pack(pady=5)
                # Clear input fields
                item_name_entry.delete(0, tk.END)
                quantity_entry.delete(0, tk.END)
                price_entry.delete(0, tk.END)
            except ValueError:
                tk.Label(add_window, text="Invalid input! Try again.", font=("Helvetica", 12), fg="red", bg="#f0f8ff").pack(pady=5)
        else:
            tk.Label(add_window, text="All fields are required!", font=("Helvetica", 12), fg="red", bg="#f0f8ff").pack(pady=5)

    # Frame for Add and Close buttons side by side
    button_frame = tk.Frame(add_window, bg="#f0f8ff")
    button_frame.pack(pady=20)

    # Add item button
    add_button = tk.Button(
        button_frame, text="Add Item", font=("Helvetica", 14), bg="#4CAF50", fg="white", command=add_item
    )
    add_button.pack(side="left", padx=(0, 0))

    # Close button
    close_button = tk.Button(
        button_frame, text="Close", font=("Helvetica", 14), bg="#f44336", fg="white", command=add_window.destroy
    )
    close_button.pack(side="left", padx=(0, 0))




# Main window
root = tk.Tk()
root.title("MyGrocer")
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
root.geometry(f"{screen_width}x{screen_height}")

root.configure(bg="#f0f8ff")

# Create the database table on program start
create_inventory_table()


# Background image for main window
background_image = Image.open(r"C:/GMS/latest groc/grocery_store.jpg")
background_image = background_image.resize((screen_width, screen_height))
background_image_tk = ImageTk.PhotoImage(background_image)

canvas = tk.Canvas(root, width=screen_width, height=screen_height)
canvas.pack(fill="both", expand=True)
canvas.create_image(0, 0, image=background_image_tk, anchor="nw")

welcome_label = tk.Label(root, text="Welcome to MyGrocer", font=("Algerian", 50, "bold"), bg="white", fg="black")
canvas.create_window(screen_width // 2, 80, window=welcome_label)

get_started_button = tk.Button(root, text="Get Started", font=("Algerian", 30),borderwidth=10, command=open_new_window)
canvas.create_window(screen_width // 2, 400, window=get_started_button)




# Run the application
root.mainloop()
