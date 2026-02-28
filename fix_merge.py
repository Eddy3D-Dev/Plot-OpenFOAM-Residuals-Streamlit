with open("streamlit_app.py", "r") as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if line.startswith("<<<<<<< Updated upstream"):
        skip = True
        continue
    if line.startswith("======="):
        if skip:
            skip = False
            continue
    if line.startswith(">>>>>>> Stashed changes"):
        new_lines.append('    else:\n        st.info("👋 Welcome! Please upload your `residual.dat` files using the uploader above to get started.")\n')
        continue
    if not skip:
        new_lines.append(line)

with open("streamlit_app.py", "w") as f:
    f.writelines(new_lines)
