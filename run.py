#!/usr/bin/env python3

# Path to the core.py file
file_path = '/content/facefusion/facefusion/uis/layouts/default.py'

# Read the content of the file
with open(file_path, 'r') as file:
    content = file.read()

# Replace the line with the updated version
updated_content = content.replace("ui.launch(show_api = False)", "ui.launch(show_api = False, share=True, enable_queue=True)")

# Write the updated content back to the file
with open(file_path, 'w') as file:
    file.write(updated_content)

from facefusion import core

if __name__ == '__main__':
    core.cli()
