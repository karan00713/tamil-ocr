from flask import Flask, request, jsonify, render_template, make_response
import json
import pytesseract
from PIL import Image
import re

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('ocr.html')

# Define the API endpoint for image processing
@app.route('/upload', methods=['POST'])
def upload():
    if 'image' in request.files:
        image = request.files['image']
        img = Image.open(image)
        img = img.convert('RGB')
        # Process the uploaded image
        output = process_image(img)
        # Perform further operations on the processed image
        json_data=json.dumps(output, ensure_ascii=False).encode('utf8')
        # Aadhar_id = output.get('Aadhar_no','output')
        # file_id = f"{Aadhar_id}.json"
        response = make_response(json_data)
        response.headers['Content-Type'] = 'application/json; charset=utf-8'
        # response.mimetype = 'application/json; charset=utf-8'
        return response
    else:
        return 'No image file found'

def extract_text(line):
    colon_index = line.find(":")
    if colon_index != -1:
        letters = line[colon_index + 1:].strip()
    return letters

def find_longest_cell(cells):
    longest_cell = ''
    max_length = 0
    
    for cell in cells[:2]:
        if len(cell) > max_length:
            longest_cell = cell
            max_length = len(cell)
    
    return longest_cell

def check_starting_string(cells):
    pattern1 = re.compile(r"ஆண்")
    pattern2 = re.compile(r"பெண்")
    pattern3 = re.compile(r"பெண்பால்")
    pattern4 = re.compile(r"ஆண்பால்")
    matching_cell = ""
    
    for cell in cells:
        if re.match(pattern1, cell):
            matching_cell = "ஆண்"
            break
        elif re.match(pattern2, cell):
            matching_cell = "பெண்"
            break
        elif re.match(pattern3, cell):
            matching_cell = "பெண்பால்"
            break
        elif re.match(pattern4, cell):
            matching_cell = "ஆண்பால்"
            break
    
    return matching_cell

def process_image(image):
    # Apply Tesseract OCR to the image and get the output text
    custom_config = r'--tessdata-dir /home/karanks/tesseract/tessdata'
    pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'
    output_text = pytesseract.image_to_string(image, lang='tam',config=custom_config)
    out = output_text.replace('\u200c','')
    out = out.splitlines()
    for i in range(len(out) - 1, -1, -1):
      if len(out[i]) <= 3:
          del out[i]
    for i in range(len(out)):
        out[i] = out[i].replace(" ", "")
    
    Name = ""
    Father_name = ""
    date = ""
    Gender = ""
    Aadhar_no = ""

    # Check if the line starts with or contains the string "தந்தை"
    for a in out:
        if a.startswith("தந்தை") or "தந்தை" in a:
            Father_name = extract_text(a)
            Father_name = re.sub(r'[:/0-9]','', Father_name)

    # Check if the line matches the date of birth pattern "dd/mm/yyyy" or "yyyy"
    for b in out:   #DOB
          # Check if the line matches the date of birth pattern "dd/mm/yyyy" or "yyyy"
          if b.startswith("பிறந்த") or "பிறந்த" in b or re.search(r':\d{2}/\d{2}/\d{4}',b) or re.search(r':\d{4}',b):
            date = extract_text(b)

    # Check if the line contains the strings "ஆண்", "பெண்", "பெண்பால்", or "ஆண்பால்"
    Gender = check_starting_string(out)

    for c in out:  #AadharNumber
        c = c.replace(" ", "")
        match = re.search(r'\d{12}$', c)
        if match:
            Aadhar_no = match.group(0)
    if len(Father_name)==0:
        Father_name = "Not available"
    Name = find_longest_cell(out)
    # Create a dictionary with the extracted information
    data = {
        "Name": Name,
        "Father_Name": Father_name,
        "Gender": Gender,
        "Aadhar_no": Aadhar_no,
        "DOB": date
    }
    # Return the extracted information
    return data

if __name__ == '__main__':
    app.run(debug=True)
