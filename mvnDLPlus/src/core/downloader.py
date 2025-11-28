import os
import requests
import zipfile
import shutil
from urllib.parse import urlparse

class Downloader:
    def __init__(self):
        self.cancel_requested = False

    def download_and_zip(self, download_targets, version, output_dir, ssl_verify=True, progress_callback=None):
        """
        Downloads multiple files and saves them as a single zip archive.
        
        Args:
            download_targets (list): List of tuples (url, filename).
            version (str): The version string.
            output_dir (str): Directory to save the final zip.
            ssl_verify (bool): Whether to verify SSL certificates.
            progress_callback (func): Callback(int) for percentage progress.
        
        Returns:
            str: Path to the created zip file.
        """
        self.cancel_requested = False
        
        temp_dir = os.path.join(output_dir, ".temp_download")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
            
        try:
            session = requests.Session()
            if not ssl_verify:
                requests.packages.urllib3.disable_warnings()
            
            downloaded_files = []
            total_files = len(download_targets)
            
            for index, (url, filename) in enumerate(download_targets):
                if self.cancel_requested:
                    raise Exception("Download cancelled by user.")
                
                # 1. Download each file
                try:
                    response = session.get(url, stream=True, verify=ssl_verify)
                    if response.status_code == 404:
                        print(f"Warning: File not found: {url}")
                        continue # Skip missing files (e.g. missing POM)
                    response.raise_for_status()
                    
                    total_size = int(response.headers.get('content-length', 0))
                    temp_file_path = os.path.join(temp_dir, filename)
                    
                    downloaded_size = 0
                    with open(temp_file_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if self.cancel_requested:
                                raise Exception("Download cancelled by user.")
                            if chunk:
                                f.write(chunk)
                                downloaded_size += len(chunk)
                                # Simple progress: (completed_files / total) + (current_file_progress / total)
                                if total_size > 0 and progress_callback:
                                    file_progress = (downloaded_size / total_size)
                                    overall_progress = int(((index + file_progress) / total_files) * 100)
                                    progress_callback(overall_progress)
                    
                    downloaded_files.append(filename)
                    
                except Exception as e:
                    print(f"Error downloading {url}: {e}")
                    # We continue trying other files unless it's a critical failure?
                    # Let's fail hard if the MAIN file (first one) fails, but maybe soft fail for POM?
                    # For now, let's raise to be safe.
                    raise e

            if not downloaded_files:
                raise Exception("No files were successfully downloaded.")

            # 2. Zip the files
            # Use the name of the first file (usually the artifact) for the zip name
            base_name = os.path.splitext(downloaded_files[0])[0]
            # If version is not in base_name, append it? Usually it is.
            final_name = f"{base_name}.zip"
            
            # Clean up filename
            final_name = "".join([c for c in final_name if c.isalpha() or c.isdigit() or c in (' ', '.', '_', '-')]).rstrip()
            final_zip_path = os.path.join(output_dir, final_name)
            
            with zipfile.ZipFile(final_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for fname in downloaded_files:
                    zipf.write(os.path.join(temp_dir, fname), arcname=fname)
            
            # Cleanup temp
            shutil.rmtree(temp_dir)
            
            if progress_callback:
                progress_callback(100)
                
            return final_zip_path

        except Exception as e:
            # Cleanup on error
            if 'temp_dir' in locals() and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            raise e

    def cancel(self):
        self.cancel_requested = True
