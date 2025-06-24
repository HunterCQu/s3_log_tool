BASE_DIR = Path("/home/hunter/drc_download_platfor")
DRC_DECODE_SCRIPT = BASE_DIR / "drc_img_decode/decode_drc_to_9.py"
drc_upload_path = BASE_DIR / "uploaded_drc"

decode_cmd = [
    "conda", "run", "-n", "data_process", "python", str(DRC_DECODE_SCRIPT),
    str(drc_upload_path),
    str(DECODE_OUT)
]
subprocess.run(decode_cmd)
