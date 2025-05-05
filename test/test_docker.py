import os
import docker

PROJECT_DIR = os.path.abspath(".")
TMP_DIR = os.path.join(PROJECT_DIR, "tmp_run")

client = docker.from_env()

container = client.containers.run(
    "jupyter/base-notebook",
    detach=True,
    ports={"8888/tcp": 8888},
    volumes={
        TMP_DIR: {'bind': '/notebook', 'mode': 'rw'}
    },
    environment={
        'JUPYTER_ENABLE_LAB': 'yes'
    },
    command=[
        "start.sh", "jupyter", "lab",
        "--LabApp.allow_origin='*'",
        "--LabApp.disable_check_xsrf=True",
        "--LabApp.tornado_settings={\"headers\": {\"Content-Security-Policy\": \"frame-ancestors *\"}}"
    ],
)

print("Jupyter avviato! Visita: http://localhost:8888")

# import os
# import shutil
# import docker

# PROJECT_DIR = os.path.abspath(".")

# NOTEBOOK_NAME = "demo.ipynb"
# NOTEBOOK_PATH = os.path.join(TMP_DIR, NOTEBOOK_NAME)

# print(f"TMP_DIR: {TMP_DIR}")

# # Pulisce/crea la directory temporanea
# if os.path.exists(TMP_DIR):
#     shutil.rmtree(TMP_DIR)
# os.makedirs(TMP_DIR)

# image_tag = "isolated-001"

# client = docker.from_env()

# print(1)

# try:
#     client.images.get(image_tag)
# except docker.errors.ImageNotFound:
#     client.images.build(path=".", dockerfile="Dockerfile", tag=image_tag)
    
# print(2)

# container = client.containers.run(
#     image_tag,
#     ports={'5000/tcp': 6000},
#     detach=True,
#     volumes={
#         TMP_DIR: {'bind': '/notebook', 'mode': 'rw'}
#     },
#     tty=True
# )

print(3)