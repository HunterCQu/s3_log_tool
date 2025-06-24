import struct
import glob
import os
import cv2
import numpy as np
import argparse
from pathlib import Path
import re
from datetime import datetime
from typing import Generator, Tuple

# === 时间处理函数 ===
def get_time_str_local(timestamp_ms: int) -> str:
    dt = datetime.fromtimestamp(timestamp_ms / 1000.0)
    return dt.strftime("%Y-%m-%d-%H%M%S-%f")[:-3]

def get_final_time_str(start_real_unix_ts: int, head_timestamp_us: int, start_sys_ts: int) -> str:
    adjusted_ts_ms = start_real_unix_ts + (head_timestamp_us) - start_sys_ts
    return get_time_str_local(adjusted_ts_ms)

def extract_unix_timestamp(value: str) -> int:
    if value is None:
        return 0
    pattern = r"(\d{8}_\d{6})"
    match = re.search(pattern, value)
    date_str = "19700101_000000"
    if match:
        date_str = match.group(1)
    try:
        dt = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
        return int(dt.timestamp() * 1000)
    except Exception as e:
        print("⚠️ 时间解析失败:", e)
        return 0

# === 结构定义 ===
LOG_HEAD_STRUCT = struct.Struct('<BBHI BBB b i 16s')
PERCEIVE_HEAD_STRUCT = struct.Struct('<BBIQ')

def extract_images_from_drc(file_path: str) -> Generator[Tuple[np.ndarray, str], None, None]:
    start_real_unix_ts = extract_unix_timestamp(os.path.splitext(os.path.basename(file_path))[0])
    _start_sys_ts = 0
    with open(file_path, 'rb') as f:
        while True:
            head_bytes = f.read(LOG_HEAD_STRUCT.size)
            if len(head_bytes) < LOG_HEAD_STRUCT.size:
                break
            unpacked = LOG_HEAD_STRUCT.unpack(head_bytes)
            real_len = unpacked[8]
            data_type = unpacked[7]
            data = f.read(real_len)
            if len(data) < real_len:
                print("⚠️ 文件中 data 长度不足，提前结束")
                break
            if data_type == 7:
                if len(data) < PERCEIVE_HEAD_STRUCT.size:
                    print("⚠️ 感知头不足，跳过该块")
                    continue
                sys_count, p_type, p_len, time_stamp = PERCEIVE_HEAD_STRUCT.unpack(data[:PERCEIVE_HEAD_STRUCT.size])
                if p_type <= 30:
                    image_data = data[PERCEIVE_HEAD_STRUCT.size:PERCEIVE_HEAD_STRUCT.size + p_len]
                    if len(image_data) != p_len:
                        print("⚠️ 图像数据长度不足")
                        continue
                    if _start_sys_ts == 0:
                        _start_sys_ts = time_stamp // 1000
                    img_array = np.frombuffer(image_data, dtype=np.uint8)
                    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                    if img is not None:
                        base_filename = get_final_time_str(start_real_unix_ts, time_stamp // 1000, _start_sys_ts)
                        # 裁剪出四张 320x272 子图
                        crop_ranges = [
                            (0, 320),
                            (321, 641),
                            (961, 1281),
                            (1281, 1601)
                        ]
                        for i, (x_start, x_end) in enumerate(crop_ranges):
                            cropped = img[:, x_start:x_end]
                            if cropped.shape[1] != 320:
                                print(f"⚠️ 跳过宽度不足的子图: {cropped.shape}")
                                continue
                            filename = f"{base_filename}_crop{i+1}.png"
                            yield cropped, filename
                    else:
                        print("❌ 图像解码失败")


def process_drc_files(src_path: str, save_dir: str):
    drc_paths = [src_path] if os.path.isfile(src_path) else glob.glob(os.path.join(src_path, "**", "*.drc"), recursive=True)
    if not drc_paths:
        print(f"⚠️ 没有找到drc文件: {src_path}")
        return
    os.makedirs(save_dir, exist_ok=True)
    total_images = 0
    for drc_path in drc_paths:
        print(f"\n处理文件: {drc_path}")
        drc_name = Path(drc_path).stem
        save_subdir = os.path.join(save_dir, drc_name)
        os.makedirs(save_subdir, exist_ok=True)
        image_count = 0
        for img, filename in extract_images_from_drc(drc_path):
            out_path = os.path.join(save_subdir, filename)
            cv2.imwrite(out_path, img)
            image_count += 1
            # print(f"✅ 图像保存为: {out_path}")
        total_images += image_count
        print(f"✅ 文件 {drc_name} 解析了 {image_count} 张图像")
    print(f"\n✅ 总共解析了 {total_images} 张图像")
    
def main():
    parser = argparse.ArgumentParser(description='解析drc文件')
    parser.add_argument('src_path', nargs='?', default="/home/hunter/drc_download_platfor/uploaded_drc",
                        help='drc文件或文件夹路径')
    parser.add_argument('save_dir', nargs='?', default="/home/hunter/drc_download_platfor/drc_img",
                        help='图像输出目录')
    args = parser.parse_args()
    process_drc_files(args.src_path, args.save_dir)


if __name__ == "__main__":
    main()
