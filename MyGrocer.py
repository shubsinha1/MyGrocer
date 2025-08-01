import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import mysql.connector
from tkinter.simpledialog import askinteger
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os
from datetime import datetime
import tkinter.filedialog as fd
import pathlib

#  connect to MySQL database
def connect_db():
    conn = mysql.connector.connect(
        host="localhost",         
        user="root",              # MySQL username
        password="shub12345", # MySQL password
        database="grocery_store"  # Database name
    )
    return conn


def insert_bill_data(SELECT_ITEM, QUANTITY, PRICE, TOTAL_PRICE):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO bills (item_name, quantity, price, total_price) VALUES (%s, %s, %s, %s)",
                   (SELECT_ITEM, QUANTITY, PRICE, TOTAL_PRICE))
    conn.commit()
    conn.close()


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


def fetch_inventory_data():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)  
    cursor.execute("SELECT * FROM inventory ORDER BY stock ASC")  
    inventory_data = cursor.fetchall() 
    conn.close()
    return inventory_data 


def refill_stock_in_db(product_name, quantity):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE inventory SET stock = stock + %s WHERE product_name = %s", (quantity, product_name))
    conn.commit()
    conn.close()


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


def reduce_stock_in_db(product_name, quantity):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE inventory SET stock = stock - %s WHERE product_name = %s AND stock >= %s", (quantity, product_name, quantity))
    conn.commit()
    conn.close()





class CustomerInfoWindow:
    def __init__(self, parent, bill_data, total_sum, cart):
        self.parent = parent
        self.bill_data = bill_data
        self.total_sum = total_sum
        self.cart = cart  # Store reference to cart
        self.bill_saved = False  # Flag to track if bill was actually saved
        
        # Create customer info window
        self.customer_window = tk.Toplevel(parent)
        self.customer_window.title("Customer Information")
        self.customer_window.geometry("600x650")
        self.customer_window.configure(bg="#f0f8ff")
        self.customer_window.resizable(False, False)
        
        # Center the window
        self.customer_window.transient(parent)
        self.customer_window.grab_set()
        
        # Title
        title_label = tk.Label(self.customer_window, text="Customer Information", 
                              font=("Helvetica", 18, "bold"), bg="#f0f8ff", fg="#333")
        title_label.pack(pady=20)
        
        # Form frame
        form_frame = tk.Frame(self.customer_window, bg="#f0f8ff")
        form_frame.pack(pady=20, padx=30)
        
        # Customer Name
        tk.Label(form_frame, text="Customer Name:", font=("Helvetica", 12), bg="#f0f8ff").pack(anchor="w")
        self.name_entry = tk.Entry(form_frame, font=("Helvetica", 12), width=30)
        self.name_entry.pack(pady=(5, 15), fill="x")
        
        # Customer Email (Optional)
        tk.Label(form_frame, text="Customer Email:", font=("Helvetica", 12), bg="#f0f8ff").pack(anchor="w")
        self.email_entry = tk.Entry(form_frame, font=("Helvetica", 12), width=30)
        self.email_entry.pack(pady=(5, 15), fill="x")
        
        # Email Configuration (Optional)
        tk.Label(form_frame, text="Store Email:", font=("Helvetica", 12), bg="#f0f8ff").pack(anchor="w")
        self.store_email_entry = tk.Entry(form_frame, font=("Helvetica", 12), width=30)
        self.store_email_entry.pack(pady=(5, 15), fill="x")
        self.store_email_entry.insert(0, "mygrocer7@gmail.com")
        
        # Store Email Password (Optional)
        tk.Label(form_frame, text="Store Email Password:", font=("Helvetica", 12), bg="#f0f8ff").pack(anchor="w")
        self.store_password_entry = tk.Entry(form_frame, font=("Helvetica", 12), width=30, show="*")
        self.store_password_entry.pack(pady=(5, 15), fill="x")
        self.store_password_entry.insert(0, "gisiyfpijdvtkdcu")
        
        # Buttons
        button_frame = tk.Frame(self.customer_window, bg="#f0f8ff")
        button_frame.pack(pady=20)
        
        save_only_button = tk.Button(button_frame, text="Save Bill Only", font=("Helvetica", 12), 
                                   bg="#2196F3", fg="white", command=self.save_bill_only)
        save_only_button.pack(side="left", padx=(0, 10))
        
        send_and_save_button = tk.Button(button_frame, text="Send & Save Bill", font=("Helvetica", 12), 
                                       bg="#4CAF50", fg="white", command=self.submit_and_send)
        send_and_save_button.pack(side="left", padx=(0, 10))
        
        # Updated cancel button to use cancel_action method
        cancel_button = tk.Button(button_frame, text="Cancel", font=("Helvetica", 12), 
                                bg="#f44336", fg="white", command=self.cancel_action)
        cancel_button.pack(side="left")

    def cancel_action(self):
        """Handle cancel button click - don't reduce stock"""
        # Simply destroy the window without any side effects
        self.customer_window.destroy()

    def save_bill_only(self):
        """Save bill without sending email"""
        customer_name = self.name_entry.get().strip()
        
        if not customer_name:
            from tkinter import messagebox
            messagebox.showerror("Error", "Customer name is required!")
            return
        
        try:
            # Generate and save bill
            bill_file_path = self.generate_and_save_bill(customer_name)
            
            # REDUCE STOCK ONLY WHEN BILL IS SAVED
            self.reduce_stock_from_bill_data()
            
            # CLEAR CART ONLY WHEN BILL IS SAVED
            self.clear_cart()
            
            # Show success message
            from tkinter import messagebox
            messagebox.showinfo("Success", f"Bill has been saved to your desktop!\nFile: {os.path.basename(bill_file_path)}")
            
            self.customer_window.destroy()
            
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to save bill: {str(e)}")

    def submit_and_send(self):
        customer_name = self.name_entry.get().strip()
        customer_email = self.email_entry.get().strip()
        store_email = self.store_email_entry.get().strip()
        store_password = self.store_password_entry.get().strip()

        # Require all fields for sending email
        if not customer_name or not customer_email or not store_email or not store_password:
            from tkinter import messagebox
            messagebox.showerror(
                "Error",
                "All fields are required to send the bill by email"
            )
            return

        # Validate email format
        if "@" not in customer_email or "." not in customer_email:
            from tkinter import messagebox
            messagebox.showerror("Error", "Please enter a valid customer email address!")
            return

        if "@" not in store_email or "." not in store_email:
            from tkinter import messagebox
            messagebox.showerror("Error", "Please enter a valid store email address!")
            return

        try:
            # Generate and save bill
            bill_file_path = self.generate_and_save_bill(customer_name)

            # Send email
            self.send_bill_email(customer_name, customer_email, store_email, store_password, bill_file_path)

            # REDUCE STOCK ONLY WHEN BILL IS SENT
            self.reduce_stock_from_bill_data()

            # CLEAR CART ONLY WHEN BILL IS SENT
            self.clear_cart()

            # Show success message
            from tkinter import messagebox
            messagebox.showinfo("Success", f"Bill has been sent to {customer_email} and saved to your desktop!")

            self.customer_window.destroy()

        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Error", f"Failed to send bill: {str(e)}")

    def generate_and_save_bill(self, customer_name):
        """Generate bill PDF and  ask user for location"""
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas as pdf_canvas
        from reportlab.lib import colors
        from tkinter import filedialog, messagebox

    
        filename = f"MyGrocer_Bill_{customer_name}.pdf"

        
        file_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=filename,
                title="Save Bill As"
            )
        if not file_path:
                raise Exception("No location selected for saving the bill.")

        # Create PDF
        c = pdf_canvas.Canvas(file_path, pagesize=letter)
        width, height = letter

        # Header
        c.setFillColor(colors.lightgrey)
        c.rect(0, height-120, width, 120, fill=True)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 36)
        c.drawString(50, height-50, "MyGrocer")
        c.setStrokeColor(colors.darkblue)
        c.setLineWidth(2)
        c.line(50, height-60, width-50, height-60)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, height-100, "INVOICE")
        current_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        c.setFont("Helvetica", 12)
        c.drawString(width-200, height-100, f"Date: {current_date}")

        # Customer info
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height-140, f"Customer Name: {customer_name}")

        # Bill content
        items_count = len(self.bill_data)
        field_height = max(400, items_count * 25 + 150)
        item_x = 70
        qty_x = 250
        price_x = 380
        total_x = 480
        total_page_height = height
        header_height = 160  # Increased for customer info
        footer_height = 150
        available_height = total_page_height - header_height - footer_height
        field_start_y = height - header_height - 50 - ((available_height - field_height) / 2)
        c.setFillColor(colors.lightgrey)
        c.rect(50, field_start_y-field_height, width-100, field_height, fill=True)
        c.setStrokeColor(colors.grey)
        c.setLineWidth(1)
        c.rect(50, field_start_y-field_height, width-100, field_height, stroke=True)
        y = field_start_y - 40
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(item_x, y, "Item")
        c.drawString(qty_x, y, "Quantity")
        c.drawString(price_x, y, "Price(Rs)")
        c.drawString(total_x, y, "Total(Rs)")
        y -= 10
        c.line(70, y, width-70, y)
        y -= 25
        c.setFont("Helvetica", 12)
        for line in self.bill_data:
            parts = line.split("\t")
            if len(parts) == 4:
                item = parts[0].strip()
                qty = parts[1].strip()
                price = parts[2].replace('₹', '').replace('', '').strip()
                total = parts[3].replace('₹', '').replace('', '').strip()
                c.drawString(item_x, y, item)
                c.drawRightString(qty_x + 80, y, qty)
                price_text = f"{price}"
                c.drawRightString(price_x + 80, y, price_text)
                total_text = f"{total}"
                c.drawRightString(total_x + 60, y, total_text)
                y -= 25
        y -= 10
        c.setStrokeColor(colors.black)
        c.line(70, y, width-70, y)
        y -= 30
        c.setFont("Helvetica-Bold", 14)
        c.drawString(item_x, y, "Grand Total(Rs):")
        grand_total_text = f"{self.total_sum:.2f}"
        c.drawRightString(total_x + 60, y, grand_total_text)
        y = 100
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawString(50, y, "Mode of Payment: UPI")
        y -= 20
        c.drawString(50, y, "Thanks for Visiting!")
        y -= 20
        c.drawString(50, y, "Store Address: Diwan Mohalla, Sarvoday Colony, Patna, Bihar")
        y -= 20
        c.drawString(50, y, "MyGrocer")
        c.save()
        return file_path

    def send_bill_email(self, customer_name, customer_email, store_email, store_password, bill_file_path):
        """Send bill PDF via email"""
        # Email configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = store_email
        msg['To'] = customer_email
        msg['Subject'] = f"Your Grocery Bill from MyGrocer - {datetime.now().strftime('%d-%m-%Y')}"
        
        # Email body
        body = f"""
Dear {customer_name},

Thank you for shopping with MyGrocer!

Please find attached your grocery bill for today's purchase.

Bill Details:
- Date: {datetime.now().strftime('%d-%m-%Y %H:%M')}
- Total Amount: ₹{self.total_sum:.2f}

If you have any queries regarding bill, feel free to reach us.

Best regards,
MyGrocer Team
Store Address: Diwan Mohalla, Sarvoday Colony, Patna, Bihar
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        with open(bill_file_path, "rb") as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {os.path.basename(bill_file_path)}'
        )
        msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(store_email, store_password)
        text = msg.as_string()
        server.sendmail(store_email, customer_email, text)
        server.quit()

    def reduce_stock_from_bill_data(self):
        """Reduce stock in database based on bill data"""
        for line in self.bill_data:
            parts = line.split("\t")
            if len(parts) == 4:
                product_name = parts[0].strip()
                quantity = int(parts[1].strip())
                reduce_stock_in_db(product_name, quantity)

    def clear_cart(self):
        """Clear the cart after successful bill creation"""
        if self.cart:
            for item in self.cart.get_children():
                self.cart.delete(item)


class MyGrocerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MyGrocer")
        
        # Get screen dimensions
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        self.root.geometry(f"{screen_width}x{screen_height}")
        self.root.configure(bg="#f0f8ff")
        
        # Create main container
        self.main_container = tk.Frame(root)
        self.main_container.pack(fill="both", expand=True)
        
        # Initialize variables
        self.cart = None
        self.inventory_data = fetch_inventory_data()
        
        # Show welcome screen
        self.show_welcome_screen()
        
        # Create database tables
        create_inventory_table()
    
        

    def clear_main_container(self):
        """Clear all widgets from main container"""
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def show_welcome_screen(self):
        """Show the welcome screen"""
        self.clear_main_container()
        
        # Load and resize background image
        try:
            background_image = Image.open(r"C:/GMS/latest groc/grocery_store.jpg")
            background_image = background_image.resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
            self.background_image_tk = ImageTk.PhotoImage(background_image)
            
            # Create canvas for background
            canvas = tk.Canvas(self.main_container, width=self.root.winfo_screenwidth(), height=self.root.winfo_screenheight())
            canvas.pack(fill="both", expand=True)
            canvas.create_image(0, 0, image=self.background_image_tk, anchor="nw")
            
            # Welcome label
            welcome_label = tk.Label(canvas, text="Welcome to MyGrocer", font=("Algerian", 50, "bold"), bg="white", fg="black")
            canvas.create_window(self.root.winfo_screenwidth() // 2, 80, window=welcome_label)
            
            # Get Started button
            get_started_button = tk.Button(canvas, text="Get Started", font=("Algerian", 30), borderwidth=10, 
                                         command=self.show_options_screen)
            canvas.create_window(self.root.winfo_screenwidth() // 2, 400, window=get_started_button)
            
        except Exception as e:
            # Fallback if image not found
            welcome_label = tk.Label(self.main_container, text="Welcome to MyGrocer", font=("Algerian", 50, "bold"), 
                                   bg="#f0f8ff", fg="black")
            welcome_label.pack(pady=100)
            
            get_started_button = tk.Button(self.main_container, text="Get Started", font=("Algerian", 30), 
                                         borderwidth=10, command=self.show_options_screen)
            get_started_button.pack(pady=50)

    def show_options_screen(self):
        """Show the options screen"""
        self.clear_main_container()
        
        # Load background image
        try:
            background_image = Image.open(r"C:/GMS/latest groc/grocery_store.jpg")
            background_image = background_image.resize((self.root.winfo_screenwidth(), self.root.winfo_screenheight()))
            self.background_image_tk = ImageTk.PhotoImage(background_image)
            
            canvas = tk.Canvas(self.main_container, width=self.root.winfo_screenwidth(), height=self.root.winfo_screenheight())
            canvas.pack(fill="both", expand=True)
            canvas.create_image(0, 0, image=self.background_image_tk, anchor="nw")
            
            # Back button
            back_button = tk.Button(canvas, text="← Back", font=("Arial", 16), bg="#EC0000", fg="white",
                                  command=self.show_welcome_screen)
            canvas.create_window(100, 50, window=back_button)
            
            # Option buttons
            generate_bill_button = tk.Button(canvas, text="GENERATE BILL", font=("Algerian", 30), 
                                           bg="#FFFFFF", fg="black", width=30, borderwidth=10,
                                           command=self.show_bill_screen)
            canvas.create_window(self.root.winfo_screenwidth() // 2, 300, window=generate_bill_button)
            
            inventory_button = tk.Button(canvas, text="OPEN INVENTORY", font=("Algerian", 30), 
                                       bg="#FFFFFF", fg="black", width=30, borderwidth=10,
                                       command=self.show_inventory_screen)
            canvas.create_window(self.root.winfo_screenwidth() // 2, 450, window=inventory_button)
            
            add_button = tk.Button(canvas, text="ADD NEW ITEM TO INVENTORY", font=("Algerian", 30), 
                                 bg="#FFFFFF", fg="black", width=30, borderwidth=10,
                                 command=self.show_add_item_screen)
            canvas.create_window(self.root.winfo_screenwidth() // 2, 600, window=add_button)
            
        except Exception as e:
            # Fallback without image
            back_button = tk.Button(self.main_container, text="← Back", font=("Arial", 16), 
                                  bg="#4CAF50", fg="white", command=self.show_welcome_screen)
            back_button.pack(anchor="nw", padx=20, pady=20)
            
            generate_bill_button = tk.Button(self.main_container, text="GENERATE BILL", font=("Algerian", 30), 
                                           bg="#FFFFFF", fg="black", width=30, borderwidth=10,
                                           command=self.show_bill_screen)
            generate_bill_button.pack(pady=50)
            
            inventory_button = tk.Button(self.main_container, text="OPEN INVENTORY", font=("Algerian", 30), 
                                       bg="#FFFFFF", fg="black", width=30, borderwidth=10,
                                       command=self.show_inventory_screen)
            inventory_button.pack(pady=50)
            
            add_button = tk.Button(self.main_container, text="ADD NEW ITEM TO INVENTORY", font=("Algerian", 30), 
                                 bg="#FFFFFF", fg="black", width=30, borderwidth=10,
                                 command=self.show_add_item_screen)
            add_button.pack(pady=50)

    def show_bill_screen(self):
        """Show the bill generation screen"""
        self.clear_main_container()
        
        # Create bill interface
        title_label = tk.Label(self.main_container, text="Grocery Billing", font=("Arial", 30, "bold"), 
                              bg="#f8f8f8", fg="#333")
        title_label.pack(pady=20)
        
        # Back button
        back_button = tk.Button(self.main_container, text="← Back to Options", font=("Arial", 16), 
                              bg="#EC0000", fg="white", command=self.show_options_screen)
        back_button.pack(anchor="nw", padx=20, pady=10)
        
        # Interface frame
        interface_frame = tk.Frame(self.main_container, bg="#fefefe", relief="groove", bd=2)
        interface_frame.pack(pady=20, padx=20, fill="both", expand=True)
        
        # Labels
        tk.Label(interface_frame, text="SELECT ITEM", font=("Helvetica", 16), bg="#fefefe").grid(row=0, column=0, padx=10, pady=10)
        tk.Label(interface_frame, text="Quantity(Kg/Unit)", font=("Helvetica", 16), bg="#fefefe").grid(row=0, column=1, padx=10, pady=10)
        tk.Label(interface_frame, text="Price (per Kg/Unit)", font=("Helvetica", 16), bg="#fefefe").grid(row=0, column=2, padx=10, pady=10)
        
        # Get inventory data
        inventory_names = [item['product_name'] for item in self.inventory_data]
        
        # Item selection
        item_name_var = tk.StringVar()
        item_name_combobox = ttk.Combobox(interface_frame, textvariable=item_name_var, values=inventory_names, 
                                         font=("Helvetica", 14), width=18, state="readonly")
        item_name_combobox.grid(row=1, column=0, padx=10, pady=10)
        
        # Quantity
        quantity_var = tk.StringVar(value="1")
        quantity_spinbox = ttk.Spinbox(interface_frame, from_=1, to=999, textvariable=quantity_var, 
                                     width=8, font=("Helvetica", 14))
        quantity_spinbox.grid(row=1, column=1, padx=10, pady=10)
        
        # Price entry
        price_entry = tk.Entry(interface_frame, font=("Helvetica", 14), borderwidth=5, width=10, state="readonly")
        price_entry.grid(row=1, column=2, padx=10, pady=10)
        
        # Item selection handler
        def on_item_selected(event):
            selected_item = item_name_var.get()
            for item in self.inventory_data:
                if item['product_name'] == selected_item:
                    price_entry.config(state="normal")
                    price_entry.delete(0, tk.END)
                    price_entry.insert(0, str(item['price']))
                    price_entry.config(state="readonly")
                    break
        item_name_combobox.bind("<<ComboboxSelected>>", on_item_selected)
        
        # Add to cart function
        def add_to_cart():
            try:
                item = item_name_var.get()
                quantity = quantity_var.get()
                price_entry.config(state="normal")
                price = price_entry.get()
                price_entry.config(state="readonly")

                if item and quantity and price:
                    try:
                        quantity = int(quantity)
                        price = float(price)
                        
                        # Check available stock
                        available_stock = None
                        for inv_item in self.inventory_data:
                            if inv_item['product_name'] == item:
                                available_stock = inv_item['stock']
                                break

                        # Calculate current quantity in cart
                        current_cart_qty = 0
                        for cart_item in self.cart.get_children():
                            values = self.cart.item(cart_item, "values")
                            if values[0] == item:
                                current_cart_qty += int(values[1])

                        if available_stock is not None and (quantity + current_cart_qty) > available_stock:
                            from tkinter import messagebox
                            messagebox.showwarning("Not enough items", "Not enough items available in Inventory.")
                            return

                        # Check if item already in cart
                        found = False
                        for cart_item in self.cart.get_children():
                            values = self.cart.item(cart_item, "values")
                            if values[0] == item:
                                new_qty = int(values[1]) + quantity
                                new_total = new_qty * price
                                self.cart.item(cart_item, values=(item, new_qty, price, new_total))
                                found = True
                                break
                        if not found:
                            total_price = quantity * price
                            self.cart.insert("", "end", values=(item, quantity, price, total_price))

                        item_name_combobox.set("")
                        quantity_var.set("1")
                        price_entry.config(state="normal")
                        price_entry.delete(0, tk.END)
                        price_entry.config(state="readonly")
                    except ValueError:
                        print("Invalid quantity or price entered.")
            except Exception as e:
                from tkinter import messagebox
                messagebox.showerror("Error", str(e))

        add_to_cart_button = tk.Button(interface_frame, text="Add to Cart", font=("Helvetica", 14), command=add_to_cart)
        add_to_cart_button.grid(row=1, column=3, padx=10, pady=10)
        
        # Cart display
        cart_label = tk.Label(interface_frame, text="Cart", font=("Algerian", 30, "bold"), bg="#fefefe")
        cart_label.grid(row=2, column=0, columnspan=4, pady=10)
        
        # Cart treeview
        self.cart = ttk.Treeview(interface_frame, columns=("Item", "Quantity(Unit/Kg)", "Price", "Total"), 
                                show="headings", height=15)
        self.cart.heading("Item", text="Item")
        self.cart.heading("Quantity(Unit/Kg)", text="Quantity(Unit/Kg)")
        self.cart.heading("Price", text="Price (per Unit/Kg)")
        self.cart.heading("Total", text="Total Price")
        
        self.cart.column("Item", width=250, anchor="w")
        self.cart.column("Quantity(Unit/Kg)", width=200, anchor="center")
        self.cart.column("Price", width=200, anchor="e")
        self.cart.column("Total", width=200, anchor="e")
        self.cart.grid(row=3, column=0, columnspan=4, padx=10, pady=10)
        
        # Create bill function
        def create_bill():
            if not self.cart.get_children():
                from tkinter import messagebox
                messagebox.showwarning("Empty Bill", "Bill cannot be empty. Add some items to proceed.")
                return
            
            # Prepare bill data
            total_sum = 0
            bill_lines = []
            for item in self.cart.get_children():
                values = self.cart.item(item, "values")
                total_sum += float(values[3])
                bill_lines.append(f"{values[0]}\t{values[1]}\t₹{values[2]}\t₹{values[3]}")
            
            # Open customer info window - DON'T CLEAR CART YET
            CustomerInfoWindow(self.root, bill_lines, total_sum, self.cart)
            
            # REMOVED: Cart clearing - will be done only when bill is saved/sent

        # Create bill button
        create_bill_button = tk.Button(interface_frame, text="Create Bill", font=("Helvetica", 16), 
                                     bg="#4CAF50", fg="white", command=create_bill)
        create_bill_button.grid(row=4, column=1, pady=10, padx=(0, 5))

    def show_inventory_screen(self):
        """Show the inventory screen"""
        self.clear_main_container()
        
        title_label = tk.Label(self.main_container, text="Inventory Overview", font=("Helvetica", 24, "bold"), 
                              bg="#f0f8ff", fg="#333333")
        title_label.pack(pady=20)
        
        # Back button
        back_button = tk.Button(self.main_container, text="← Back to Options", font=("Arial", 16), 
                              bg="#EC0000", fg="white", command=self.show_options_screen)
        back_button.pack(anchor="nw", padx=20, pady=10)
        
        # Refresh inventory data
        self.inventory_data = fetch_inventory_data()
        
        table_frame = tk.Frame(self.main_container, bg="#ffffff")
        table_frame.pack(pady=20, padx=30, fill="both", expand=True)
        
        canvas = tk.Canvas(table_frame, bg="#ffffff")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollable_frame = tk.Frame(canvas, bg="#ffffff")
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        heading_font = ("Helvetica", 16, "bold")
        tk.Label(scrollable_frame, text="Product", font=heading_font, bg="#ffffff").grid(row=0, column=0, padx=10, pady=10)
        tk.Label(scrollable_frame, text="Stock Available", font=heading_font, bg="#ffffff").grid(row=0, column=1, padx=10, pady=10)
        tk.Label(scrollable_frame, text="Price", font=heading_font, bg="#ffffff").grid(row=0, column=2, padx=10, pady=10)
        tk.Label(scrollable_frame, text="Action", font=heading_font, bg="#ffffff").grid(row=0, column=3, padx=10, pady=10)
        
        def refill_stock(product_name, label):
            quantity = askinteger("Refill Stock", f"Enter quantity to add for {product_name}:", minvalue=1)
            if quantity is not None:
                for item in self.inventory_data:
                    if item["product_name"] == product_name:
                        item["stock"] += quantity
                        label.config(text=str(item["stock"]))
                        break
                
                current_price = next((item["price"] for item in self.inventory_data if item["product_name"] == product_name), 0)
                add_items_to_stock(product_name, quantity, current_price)
        
        for idx, item in enumerate(self.inventory_data, start=1):
            product = item["product_name"]
            stock = item["stock"]
            price = item["price"]
            
            tk.Label(scrollable_frame, text=product, font=("Helvetica", 14), bg="#ffffff").grid(row=idx, column=0, padx=10, pady=10)
            
            stock_label = tk.Label(scrollable_frame, text=stock, font=("Helvetica", 14), bg="#ffffff")
            stock_label.grid(row=idx, column=1, padx=10, pady=10)
            
            tk.Label(scrollable_frame, text=f"₹{price:.2f}", font=("Helvetica", 14), bg="#ffffff").grid(row=idx, column=2, padx=10, pady=10)
            
            refill_button = tk.Button(scrollable_frame, text="Refill", font=("Helvetica", 12), 
                                    bg="#4CAF50", fg="white", 
                                    command=lambda p=product, lbl=stock_label: refill_stock(p, lbl))
            refill_button.grid(row=idx, column=3, padx=10, pady=10)

    def show_add_item_screen(self):
        """Show the add item screen"""
        self.clear_main_container()
        
        title_label = tk.Label(self.main_container, text="Add New Item to Stock", font=("Helvetica", 18, "bold"), 
                              bg="#f0f8ff")
        title_label.pack(pady=20)
        
        # Back button
        back_button = tk.Button(self.main_container, text="← Back to Options", font=("Arial", 16), 
                              bg="#EC0000", fg="white", command=self.show_options_screen)
        back_button.pack(anchor="nw", padx=20, pady=10)
        
        # Form frame
        form_frame = tk.Frame(self.main_container, bg="#f0f8ff")
        form_frame.pack(pady=20)
        
        tk.Label(form_frame, text="Item Name:", font=("Helvetica", 14), bg="#f0f8ff").pack(pady=5)
        item_name_entry = tk.Entry(form_frame, font=("Helvetica", 12))
        item_name_entry.pack(pady=5)
        
        tk.Label(form_frame, text="Quantity:", font=("Helvetica", 14), bg="#f0f8ff").pack(pady=5)
        quantity_entry = tk.Entry(form_frame, font=("Helvetica", 12))
        quantity_entry.pack(pady=5)
        
        tk.Label(form_frame, text="Price per Unit:", font=("Helvetica", 14), bg="#f0f8ff").pack(pady=5)
        price_entry = tk.Entry(form_frame, font=("Helvetica", 12))
        price_entry.pack(pady=5)
        
        def add_item():
            item_name = item_name_entry.get()
            quantity = quantity_entry.get()
            price = price_entry.get()
            if item_name and quantity and price:
                try:
                    quantity = int(quantity)
                    price = float(price)
                    add_items_to_stock(item_name, quantity, price)
                    
                    # Refresh inventory data
                    self.inventory_data = fetch_inventory_data()
                    
                    # Show success message
                    success_label = tk.Label(form_frame, text=f"Added: {item_name} (Quantity: {quantity}, Price: ₹{price:.2f})", 
                                           font=("Helvetica", 12), bg="#f0f8ff", fg="green")
                    success_label.pack(pady=5)
                    
                    # Clear entries
                    item_name_entry.delete(0, tk.END)
                    quantity_entry.delete(0, tk.END)
                    price_entry.delete(0, tk.END)
                    
                    # Remove success message after 3 seconds
                    self.root.after(3000, success_label.destroy)
                    
                except ValueError:
                    error_label = tk.Label(form_frame, text="Invalid input! Try again.", font=("Helvetica", 12), 
                                         fg="red", bg="#f0f8ff")
                    error_label.pack(pady=5)
                    self.root.after(3000, error_label.destroy)
            else:
                error_label = tk.Label(form_frame, text="All fields are required!", font=("Helvetica", 12), 
                                     fg="red", bg="#f0f8ff")
                error_label.pack(pady=5)
                self.root.after(3000, error_label.destroy)
        
        button_frame = tk.Frame(self.main_container, bg="#f0f8ff")
        button_frame.pack(pady=20)
        
        add_button = tk.Button(button_frame, text="Add Item", font=("Helvetica", 14), 
                             bg="#4CAF50", fg="white", command=add_item)
        add_button.pack(side="left", padx=(0, 10))

# Main execution
if __name__ == "__main__":
    root = tk.Tk()
    app = MyGrocerApp(root)
    root.mainloop()
