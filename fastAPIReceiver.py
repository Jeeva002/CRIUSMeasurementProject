import requests
import os
from pathlib import Path

def download_zip_file(server_url, endpoint, output_path=None, headers=None):
    """
    Download a zip file from a FastAPI server
    
    Args:
        server_url (str): Base URL of the FastAPI server
        endpoint (str): Endpoint path for the zip file
        output_path (str): Local path to save the zip file
        headers (dict): Optional headers for authentication
    
    Returns:
        bool: True if download successful, False otherwise
    """
    try:
        # Construct full URL
        full_url = f"{server_url.rstrip('/')}/{endpoint.lstrip('/')}"
        
        # Default headers
        if headers is None:
            headers = {}
        
        # Make the request
        print(f"Downloading from: {full_url}")
        response = requests.get(full_url, headers=headers, stream=True)
        
        # Check if request was successful
        response.raise_for_status()
        
        # Determine output filename
        if output_path is None:
            # Try to get filename from Content-Disposition header
            content_disposition = response.headers.get('Content-Disposition', '')
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
            else:
                filename = 'downloaded_file.zip'
            output_path = filename
        
        # Create directory if it doesn't exist
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Download and save the file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        file_size = os.path.getsize(output_path)
        print(f"Download completed: {output_path} ({file_size} bytes)")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def main():
    # Configuration
    SERVER_URL = "https://your-fastapi-server.amazonaws.com"  # Replace with your server URL
    ENDPOINT = "/download/zipfile"  # Replace with your endpoint
    OUTPUT_PATH = "downloaded_file.zip"  # Local path to save the file
    
    # Optional: Add authentication headers if needed
    headers = {
        # "Authorization": "Bearer your_token_here",
        # "X-API-Key": "your_api_key_here"
    }
    
    # Download the file
    success = download_zip_file(
        server_url=SERVER_URL,
        endpoint=ENDPOINT,
        output_path=OUTPUT_PATH,
        headers=headers
    )
    
    if success:
        print("Zip file downloaded successfully!")
        

   
    else:
        print("Failed to download zip file.")


if __name__ == "__main__":
    main()