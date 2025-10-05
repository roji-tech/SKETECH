import random
from datetime import datetime

def generate_student_id(school_name):
    # Generate a prefix from the first 3 letters of the school name
    school_code = school_name[:3].upper()

    # Get the last two digits of the current year
    current_year = str(datetime.now().year)[-2:]

    # Generate a random 4-digit number
    random_number = str(random.randint(1000, 9999))

    # Combine to form the student ID
    student_id = f"{school_code}-{current_year}-{random_number}"
    
    return student_id
