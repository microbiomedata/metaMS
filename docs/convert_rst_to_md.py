import pypandoc

def convert_rst_to_md(input_file, output_file):
    # Convert RST to Markdown
    output = pypandoc.convert_file(input_file, 'md', format='rst')
    
    # Write the output to the MD file
    with open(output_file, 'w') as f:
        f.write(output)

if __name__ == "__main__":
    input_file = 'docs/index_lipid.rst'
    output_file = 'docs/README_LCMS_LIPID.md'
    convert_rst_to_md(input_file, output_file)