
from fastapi import FastAPI,Form,UploadFile,File
import pandas as pd
from fastapi.responses import HTMLResponse,RedirectResponse
import uvicorn
import sqlite3



app = FastAPI()
DATABASE = 'data.db'
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contacts (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            Fullname TEXT,
            Email TEXT,
            country_code INTEGER,
            phone_number TEXT,
            identification_number TEXT,
            Gender TEXT
        )
    ''')
    conn.commit()
    conn.close()

    
init_db()
@app.get("/",response_class=HTMLResponse)
def contact_form(page: int = 1):
    page_size = 5
    offset = (page - 1) * page_size
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT count(*) FROM contacts')
    total_contacts = cursor.fetchone()[0]

    cursor.execute("SELECT * FROM contacts LIMIT ? OFFSET ?", (page_size, offset))
    rows = cursor.fetchall()
    conn.close()
    html="""
    <html>
        <body>
            <h2>Contact Form</h2>
            <form action="/upload_excel" method="post" enctype="multipart/form-data">
            <h3>Upload Excel File (Student List)</h3>
            <input type="file" name="file" accept=".xlsx" required>
            <input type="submit" value="Upload Excel">
            </form>
            <br><br>

            <form action="/add" method="post">
                Fullname: <input type="text" name="Fullname" required ><br><br>
                Email: <input type="text" name="Email" required><br><br>
                 Country Code:
                 <select name="country_code" required>
                <option value="+1">+1 (USA)</option>
                <option value="+44">+44 (UK)</option>
                <option value="+91">+91 (India)</option>
                <option value="+61">+61 (Australia)</option>
                </select><br><br>
                phone_Number: <input type="text" name="phone_number" required><br><br>
                Identification_Number: <input type="text" name="identification_number" required><br><br>
                gender: <input type="text" name="Gender" required><br><br>
                <input type="submit" value="Add Contact"><br><br>
            </form>
            <form action="/search" method="get">
                Search Contact:
                <input type="text" name="search_contact">
                <input type="submit" value="Search Contact"><br><br>
            </form>
            <h2>Contact List</h2>
            <table border="1">
                <tr>
                    <th>ID</th>
                    <th>Fullname</th>
                    <th>Email</th>
                    <th>Country Code</th>
                    <th>Phone Number</th>
                    <th>Identification Number</th>
                    <th>Gender</th> 
                    <th>Action</th>
                </tr>"""
    for row in rows: 
        html += f"""
                <tr>
                    <td>{row[0]}</td>
                    <td>{row[1]}</td>
                    <td>{row[2]}</td>
                    <td>{row[3]}</td>
                    <td>{row[4]}</td>
                    <td>{row[5]}</td>
                    <td>{row[6]}</td>
                    <td>
                        <form action="/delete/{row[5]}" method="post" style="display:inline;">
                            <input type="submit" value="Delete">
                        </form>
                    </td>
                </tr>"""
        
    html += """
            </table>                                          
        </body>
    </html>"""
    pagenation_html = "<div>"
    total_pages = (total_contacts+ page_size - 1) // page_size
    if page > 1:
        pagenation_html += f"<a href='/?page={page-1}'><button>Previous</button></a> "
    for p in range(1, total_pages + 1):
        if p == page:
            pagenation_html += f"<strong><button>{p}</button></strong> "
    if page < total_pages:
        pagenation_html += f"<a href='/?page={page+1}'><button>Next</button></a>"
    pagenation_html += "</div>"
    html += pagenation_html
    

    return HTMLResponse(html)
@app.post("/upload_excel")
def upload_excel(file: UploadFile = File(...)):
    if not file.filename.endswith(".xlsx"):
        return HTMLResponse("<h3>Only .xlsx Excel files are supported</h3>")

    # Read Excel into Pandas
    df = pd.read_excel(file.file)

    # REQUIRED COLUMNS IN EXCEL
    required_columns = ["Fullname", "Email", "country_code", "phone_number", "identification_number", "Gender"]

    # Validate columns
    for col in required_columns:
        if col not in df.columns:
            return HTMLResponse(f"<h3>Missing column in Excel: {col}</h3>")

    df = df.drop_duplicates(subset=["Email", "phone_number"], keep="first")

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    inserted_rows = 0
    skipped_duplicates = 0
    # Insert each row into DB
    for  _, row in df.iterrows():
        cursor.execute("""
            SELECT COUNT(*) FROM contacts
            WHERE Email = ? OR phone_number = ?
        """, (row["Email"], row["phone_number"]))
        
        exists = cursor.fetchone()[0]

        if exists:
            skipped_duplicates += 1
            continue
        cursor.execute("""
            INSERT INTO contacts (Fullname, Email, country_code, phone_number, identification_number, Gender)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            row["Fullname"],
            row["Email"],
            row["country_code"],
            row["phone_number"],
            row["identification_number"],
            row["Gender"]
        ))
        inserted_rows += 1

    conn.commit()
    conn.close()

    return HTMLResponse(f"""
        <html>
            <body>
                <h2>Excel Upload Successful</h2>
                <p>{inserted_rows} contacts inserted into database.</p>
                <p>{skipped_duplicates} duplicates skipped.</p>
                <button><a href="/">Go Back</a></button>
            </body>
        </html>
    """)

@app.post("/add")
def add(Fullname: str = Form(...), Email: str = Form(...), country_code: str = Form(...), phone_number: str = Form(...), identification_number: str = Form(...), Gender : str = Form(...)):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO contacts(Fullname, Email, country_code, phone_number, identification_number, Gender)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (Fullname, Email, country_code, phone_number, identification_number, Gender))
    conn.commit()    
    conn.close()
    return RedirectResponse("/", status_code=303)

@app.post("/delete/{identification_number}")
def delete(identification_number: str):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM contacts WHERE identification_number=?', (identification_number,))
    conn.commit()
    conn.close()
    return RedirectResponse("/", status_code=303)
    
@app.get("/search", response_class=HTMLResponse)
def search(search_contact: str, page: int = 1):
    q = search_contact
    page_size = 5
    offset = (page - 1) * page_size

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    like_pattern = f"%{q}%"
    cursor.execute("""
        SELECT COUNT(*) FROM contacts
        WHERE 
            Fullname LIKE ? OR
            email LIKE ? OR
            phone_number LIKE ? OR
            country_code LIKE ? OR
            identification_number LIKE ? OR
            gender LIKE ?
    """, (like_pattern, like_pattern, like_pattern, like_pattern, like_pattern, like_pattern))
    total_results = cursor.fetchone()[0]
    cursor.execute("""
        SELECT * FROM contacts
        WHERE 
            ID LIKE ? OR
            Fullname LIKE ? OR
            email LIKE ? OR
            phone_number LIKE ? OR
            country_code LIKE ? OR
            identification_number LIKE ? OR
            gender LIKE ?
        LIMIT ? OFFSET ?
    """, (like_pattern,like_pattern,like_pattern,like_pattern,like_pattern,like_pattern,like_pattern, page_size, offset))
    results = cursor.fetchall()

    conn.close()

    # Render HTML
    html = "<html><body><h2>Search Results</h2>"

    if results:
        html += """
        <table border="1">
            <tr>
                <th>ID</th>
                <th>Fullname</th>
                <th>Email</th>
                <th>Phone Number</th>
                <th>Country Code</th>
                <th>Identification Number</th>
                <th>Gender</th>
            </tr>
        """

        for row in results:
            html += f"""
            <tr>
                <td>{row['ID']}</td>
                <td>{row['Fullname']}</td>
                <td>{row['email']}</td>
                <td>{row['phone_number']}</td>
                <td>{row['country_code']}</td>
                <td>{row['identification_number']}</td>
                <td>{row['gender']}</td>
            </tr>
            """

        html += "</table><br>"
        # Pagination links
        html += "<div>"
        if page > 1:
            html += f"<a href='/search?search_contact={q}&page={page-1}&page_size={page_size}'><button>Previous</button></a> "
        total_pages = (total_results + page_size - 1) // page_size
        for p in range(1, total_pages + 1):
            if p == page:
                html += f"<strong><button>{p}</button></strong> "

        if page < total_pages:
            html += f"<a href='/search?search_contact={q}&page={page+1}&page_size={page_size}'><button>Next</button></a>"
        html += "</div>"

                
        html += """
                </table>
                <br><a href="/"><button>Back to Home</button></a>
            </body>
        </html>"""
        return HTMLResponse(html)
    else:
        return HTMLResponse("""
        <html>
            <body>
                <h2>No results found.</h2>
                <br><button><a href="/">Back to Home</a></button>
            </body>
        </html>""")




#Terminal 
def read_contacts():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts')
    rows = cursor.fetchall()
    conn.close()
    return rows
def update_contact(identification_number: str, Fullname: str = None, Email: str = None, country_code: str = None, phone_number: str = None, Gender : str = None):

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM contacts WHERE identification_number=?', (identification_number,))
    row = cursor.fetchone()
    if row:
        updated_Fullname = Fullname if Fullname is not None else row[1]
        updated_Email = Email if Email is not None else row[2]
        updated_country_code = country_code if country_code is not None else row[3]
        updated_phone_number = phone_number if phone_number is not None else row[4]
        updated_Gender = Gender if Gender is not None else row[6]   
        cursor.execute('''
            UPDATE contacts
            SET Fullname=?, Email=?, country_code=?, phone_number=?, Gender=?
            WHERE identification_number=?
        ''', (updated_Fullname, updated_Email, updated_country_code, updated_phone_number, updated_Gender, identification_number))  
        conn.commit()
    conn.close()

def delete_contact(identification_number: str):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM contacts WHERE identification_number=?', (identification_number,))
    conn.commit()
    conn.close()

def menu():
    print("Contact Management System")
    print("1. Add Contact")
    print("2. View Contacts")
    print("3. Update Contact")
    print("4. Delete Contact")
    print("5. web")
    print("6. Exit")
    while True:
        choice = input("Enter your choice: ")
        if choice == '1':
            Fullname = input("Enter Fullname: ")
            Email = input("Enter Email: ")
            country_code = input("Enter Country Code: ")
            phone_number = input("Enter Phone Number: ")
            identification_number = input("Enter Identification Number: ")
            gender = input("Enter Gender: ")
            add(Fullname,Email,country_code, phone_number, identification_number, gender)
            print("Contact added successfully.")    
        elif choice == '2':
            contacts = read_contacts()
            for contact in contacts:
                print(contact)
        elif choice == '3':
            identification_number = input("Enter Identification Number of the contact to update: ")
            Fullname = input("Enter new Fullname (leave blank to keep unchanged): ")
            Email = input("Enter new Email (leave blank to keep unchanged): ")
            country_code = input("Enter new Country Code (leave blank to keep unchanged): ")
            phone_number = input("Enter new Phone Number (leave blank to keep unchanged): ")
            gender = input("Enter new Gender (leave blank to keep unchanged): ")
            update_contact(identification_number, Fullname or None, Email or None, country_code or None, phone_number or None, gender or None)
            print("Contact updated successfully.")
        elif choice == '4':
            identification_number = input("Enter Identification Number of the contact to delete: ")
            delete_contact(identification_number)
            print("Contact deleted successfully.")
        elif choice == '5':
            print("Starting web server...")
            uvicorn.run(app, host="127.0.0.1", port=8006)
        elif choice == '6':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")
if __name__ == "__main__":
    menu() 


