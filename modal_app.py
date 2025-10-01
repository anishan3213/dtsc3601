import modal

app = modal.App("llm-etl-streamlit")

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("streamlit", "pandas", "supabase", "python-dotenv")
    # copy your file into the container
    .add_local_file("streamlit_app.py", remote_path="/root/streamlit_app.py")
)

secret = modal.Secret.from_name("my-secret")

@app.function(image=image, secrets=[secret])
@modal.web_server(port=8501)
def serve():
    import subprocess
    # run the file at the path we just copied
    return subprocess.Popen([
        "streamlit", "run", "/root/streamlit_app.py",
        "--server.port", "8501",
        "--server.headless", "true",
    ])
