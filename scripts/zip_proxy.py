import os
import zipfile
import sys

def zip_proxy(source_dir, output_filename):
    """
    Zips the given source directory into the output filename.
    """
    # Ensure source exists using absolute path check or relative
    if not os.path.isdir(source_dir):
        print(f"Error: Source directory '{source_dir}' does not exist.")
        sys.exit(1)

    print(f"Zipping '{source_dir}' to '{output_filename}'...")
    
    with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Archive name should be relative to the source directory
                # e.g., if source is 'build_temp/apiproxy', file 'build_temp/apiproxy/proxies/default.xml'
                # should be stored as 'proxies/default.xml' INSIDE 'apiproxy/'?
                # Standard Apigee bundle structure:
                # root/
                #   apiproxy/
                #     proxies/
                #     targets/
                #     ...
                
                # If we are passing "build_temp/apiproxy" as source, we want the ZIP to contain "apiproxy/..."
                # So relative path calculation depends on parent of source_dir
                
                # Let's assume input is the 'apiproxy' folder itself.
                # Apigee expects the zip to optionally contain the 'apiproxy' folder at root, OR just the contents.
                # Best practice: ZIP structure = apiproxy/proxies/... 
                
                rel_path = os.path.relpath(file_path, os.path.dirname(source_dir))
                # Force forward slashes for portability
                rel_path = rel_path.replace(os.path.sep, '/')
                zipf.write(file_path, rel_path)

    print(f"Successfully created '{output_filename}'")

if __name__ == "__main__":
    # Support args: python zip_proxy.py [source_dir] [zip_path]
    # Default behavior (legacy): specific hardcoded paths
    
    if len(sys.argv) >= 3:
        src = sys.argv[1]
        dst = sys.argv[2]
    else:
        # Fallback to defaults if no args provided (for backward compat if needed, though we should avoid)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, ".."))
        src = os.path.join(project_root, "apigee", "proxies", "investment-agent-mcp", "apiproxy")
        dst = os.path.join(project_root, "apigee", "proxies", "investment-agent-mcp.zip")

    zip_proxy(src, dst)
