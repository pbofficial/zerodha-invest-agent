import zipfile
import os

def zip_apigee(source_dir, output_zip):
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Create the arcname with forward slashes
                # Ensure the path starts with 'apiproxy/'
                rel_path = os.path.relpath(file_path, os.path.join(source_dir, ".."))
                arcname = rel_path.replace(os.sep, '/')
                zipf.write(file_path, arcname)
    print(f"Successfully created {output_zip} with forward slashes.")

if __name__ == "__main__":
    src = "apigee/proxies/investment-agent-mcp/apiproxy"
    out = "apigee/proxies/investment-agent-mcp.zip"
    zip_apigee(src, out)
