import gspread
from oauth2client.service_account import ServiceAccountCredentials

def connect_sheet():

    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", scope
    )

    client = gspread.authorize(creds)
    sheet = client.open("Leads").sheet1

    return sheet


def get_all_data(sheet):
    return sheet.get_all_records()


def find_existing(sheet, email):
    records = sheet.get_all_records()

    for idx, row in enumerate(records, start=2):
        if row["Email"] == email:
            return idx

    return None


def save_or_update(sheet, data):
    """
    data = [Company, Website, Industry, Email, Status]
    """

    row_index = find_existing(sheet, data[3])

    if row_index:
        # Update existing row
        sheet.update(f"A{row_index}:E{row_index}", [data])
        return "updated"

    else:
        sheet.append_row(data)
        return "new"