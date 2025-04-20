import os
import re

def remove_csrf_tokens(directory="templates"):
    """Remove CSRF token inputs from all HTML files in the specified directory."""
    csrf_pattern = re.compile(r'<input\s+type="hidden"\s+name="csrf_token"\s+value="\{\{\s*csrf_token\(\)\s*\}\}">')
    
    # Get all HTML files in the templates directory
    html_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith('.html')]
    
    for file_path in html_files:
        try:
            # Read file content
            with open(file_path, 'r') as file:
                content = file.read()
            
            # Find and remove CSRF token inputs
            matches = csrf_pattern.findall(content)
            if matches:
                print(f"Removing {len(matches)} CSRF tokens from {file_path}")
                modified_content = csrf_pattern.sub('', content)
                
                # Write modified content back to file
                with open(file_path, 'w') as file:
                    file.write(modified_content)
            else:
                print(f"No CSRF tokens found in {file_path}")
                
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

if __name__ == "__main__":
    print("Starting CSRF token removal...")
    remove_csrf_tokens()
    print("Finished removing CSRF tokens from templates.") 