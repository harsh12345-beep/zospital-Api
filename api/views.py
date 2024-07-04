from rest_framework.decorators import api_view
from .serializers import PDFDataSerializer
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
import os
from django.http import HttpResponse
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from django.shortcuts import render
from django.http import HttpResponse
from django.http import HttpResponse
from rest_framework.decorators import api_view
from .serializers import PDFDataSerializer
from pyhtml2pdf import converter
from django.conf import settings
from bs4 import BeautifulSoup
from google.oauth2 import service_account


SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDS_PATH = 'path/to/credentials.json'



def pdf_form(request):
    return render(request, 'api/form.html')

def pdfview(request):
    return render(request, 'api/pdf_template.html')
# Function to get Google Drive service
def get_drive_service(credentials_file):
    SCOPES = ['https://www.googleapis.com/auth/drive']
    credentials = service_account.Credentials.from_service_account_file(
        credentials_file, scopes=SCOPES)
    return build('drive', 'v3', credentials=credentials)

# Function to upload file to Google Drive
def upload_to_google_drive(file_path, credentials_file):
    service = get_drive_service(credentials_file)
    file_name = os.path.basename(file_path)
    file_metadata = {'name': file_name}
    media = MediaFileUpload(file_path, resumable=True)
    try:
        file = service.files().create(body=file_metadata,
                                      media_body=media,
                                      fields='id').execute()
        return file.get('id')
    except Exception as e:
        print(f"Error uploading file to Google Drive: {str(e)}")
        return None

# Function to grant permission to a Gmail account for a specific file
def grant_drive_permission(file_id, email, credentials_file, role='reader'):
    service = get_drive_service(credentials_file)
    permission = {
        'type': 'user',
        'role': role,
        'emailAddress': email
    }
    try:
        permission = service.permissions().create(
            fileId=file_id,
            body=permission,
            fields='id'
        ).execute()
        print(f'Permission ID: {permission.get("id")}')
    except Exception as e:
        print(f'Error granting permission: {str(e)}')




@api_view(['POST'])
def create_pdf_api(request):
    serializer = PDFDataSerializer(data=request.data)
    if serializer.is_valid():
        data = serializer.validated_data
        patient_name = data.get('name', 'patient')

        # Render the HTML template
        html_string = render_to_string('api/pdf_template.html', data)

        # Parse the HTML and replace static file paths
        soup = BeautifulSoup(html_string, 'html.parser')
        for img in soup.find_all('img'):
            if img.attrs.get('src', '').startswith('/static/'):
                img['src'] = './static/' + img['src'].split('/static/')[1]
        for div in soup.find_all('div'):
            style = div.attrs.get('style', '')
            if 'background-image' in style:
                start_index = style.find('url(') + 4
                end_index = style.find(')', start_index)
                static_path = style[start_index:end_index].strip("'\"")
                if static_path.startswith('/static/'):
                    new_path = './static/' + static_path.split('/static/')[1]
                    div['style'] = style[:start_index] + new_path + style[end_index:]

        # Write to temporary HTML file
        html_string = str(soup)
        html_file_path = os.path.join(settings.BASE_DIR, 'temp.html')
        with open(html_file_path, 'w') as html_file:
            html_file.write(html_string)

        # Ensure the PDFs directory exists
        pdf_dir = os.path.join(settings.BASE_DIR, 'pdfs')
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)

        # Convert HTML to PDF using pyhtml2pdf
        pdf_filename = f"{patient_name.replace(' ', '_')}_report.pdf"
        pdf_file_path = os.path.join(pdf_dir, pdf_filename)
        converter.convert(f'file:///{html_file_path}', pdf_file_path)

        # Upload PDF to Google Drive
        credentials_file = os.path.join(settings.BASE_DIR, 'credentials.json')
        file_id = upload_to_google_drive(pdf_file_path, credentials_file)

        # Grant permission to Gmail account to view the file
        gmail_email = 'geekymolecules.nikhil@gmail.com'  # Replace with your Gmail email
        grant_drive_permission(file_id, gmail_email, credentials_file)

        # Serve the PDF as a response
        with open(pdf_file_path, 'rb') as pdf_file:
            response = HttpResponse(pdf_file.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{pdf_filename}"'
            return response
    else:
        return JsonResponse(serializer.errors, status=400)
