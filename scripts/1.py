# import os
# import struct
# import numpy as np
# import cv2
# import logging
# from datetime import datetime

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# class PerceiveHead:
#     def __init__(self, sys_count, type_, length, timestamp):
#         self.sys_count = sys_count
#         self.type = type_
#         self.length = length
#         self.timestamp = timestamp


# class PerceiveResultParser:
#     def __init__(self):
#         self.head = None
#         self._perceive_result_data = bytearray(1024 * 1024)
#         self.has_new_data = False

#     def process_data(self, data, offset, length):
#         head_size = 16  # Size of PerceiveHead structure
#         if offset + head_size > length:
#             return
        
#         # Read header correctly using struct.unpack
#         self.head = PerceiveHead(
#             *struct.unpack('<BBIQ', data[offset:offset + head_size])
#         )
#         offset += head_size

#         if self.head.length + head_size > length:
#             return

#         # Copy body data
#         self._perceive_result_data[:self.head.length] = data[offset:offset + self.head.length]
#         self.has_new_data = True

#     def update(self, data, length):
#         self.process_data(data, 0, length)

#     @property
#     def perceive_result_data(self):
#         return self._perceive_result_data

#     @perceive_result_data.setter
#     def perceive_result_data(self, value):
#         self._perceive_result_data = value


# class SavePicture:
#     def __init__(self):
#         self._start_real_unix_ts = 0
#         self._start_sys_ts = 0
#         self._parser = PerceiveResultParser()
#         self.record_dir = None  # Directory to save images

#     def cal_edge_cnt(self, num):
#         for i in range(1, num + 1):
#             if i * i >= num:
#                 return i
#         return 0

#     def reshape_mat(self, input_mat):
#         h, w = input_mat.shape[:2]
#         single_w, single_h = 320, h
#         edge_num = self.cal_edge_cnt(w // single_w)
#         ret = np.zeros((single_h * edge_num, single_w * edge_num, input_mat.shape[2]), dtype=np.uint8)

#         for i in range(w // single_w):
#             dest_i, dest_j = divmod(i, edge_num)
#             dest = ret[dest_i * single_h:(dest_i + 1) * single_h, dest_j * single_w:(dest_j + 1) * single_w]
#             source_rec = input_mat[:, i * single_w:(i + 1) * single_w]
#             dest[:] = source_rec
#         return ret

#     def save(self, records):
#         if self.record_dir is None:
#             logger.error("record_dir is not set. Cannot save images.")
#             return False

#         if not os.path.exists(self.record_dir):
#             os.makedirs(self.record_dir, exist_ok=True)

#         self._start_sys_ts = 0
#         for record in records:
#             self._parser.update(record.data, record.real_len)
#             if not self._parser.has_new_data:
#                 continue

#             if self._parser.head.type > 30:
#                 continue

#             if self._start_sys_ts == 0:
#                 self._start_sys_ts = self._parser.head.timestamp // 1000

#             if self._start_real_unix_ts == 0:
#                 self._start_real_unix_ts = int(datetime.now().timestamp())

#             # Generate image filename
#             file_name = f"image_{self._start_real_unix_ts + self._parser.head.timestamp // 1000 - self._start_sys_ts}.png"
#             file_path = os.path.join(self.record_dir, file_name)

#             img_data = self._parser.perceive_result_data[:self._parser.head.length]
#             image_mat = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)

#             if image_mat is None or image_mat.size == 0:
#                 logger.warning(f"Failed to decode image, skipping {file_name}")
#                 continue

#             # Reshape and save the image
#             new_mat = self.reshape_mat(image_mat)
#             cv2.imwrite(file_path, new_mat)
#             logger.info(f"Saved image: {file_path}")

#         return True


# class RecordPackage:
#     def __init__(self, data, real_len):
#         self.data = data
#         self.real_len = real_len


# class RecordDataParser:
#     def __init__(self):
#         self._recordPackages = []

#     def parse_package(self, file_name: str) -> bool:
#         if not os.path.exists(file_name):
#             logger.error(f"File not found: {file_name}")
#             return False
        
#         self._recordPackages.clear()
#         header_size = 24  # Adjust based on actual LogHeader size

#         try:
#             with open(file_name, 'rb') as fs:
#                 while True:
#                     head_buf = fs.read(header_size)
#                     if not head_buf:
#                         break

#                     # Read additional module information
#                     mod_id = fs.read(1)
#                     mod_offset = fs.read(1)
#                     mod_len_bytes = fs.read(4)

#                     if not mod_len_bytes or len(mod_len_bytes) < 4:
#                         break

#                     mod_len = struct.unpack('<I', mod_len_bytes)[0]
#                     data = head_buf + mod_id + mod_offset + mod_len_bytes + fs.read(mod_len)
#                     self._recordPackages.append(RecordPackage(data, mod_len))
            
#             logger.info(f"Parsed {len(self._recordPackages)} record packages from {file_name}")
#             return True

#         except Exception as e:
#             logger.error(f"Error reading file {file_name}: {e}")
#             return False


# # Example usage to process .drc file
# def process_drc_file(file_name: str, save_dir: str):
#     parser = RecordDataParser()
#     if not parser.parse_package(file_name):
#         logger.error("Failed to parse the package.")
#         return

#     save_picture = SavePicture()
#     save_picture.record_dir = save_dir  # Set directory for saving images
#     if save_picture.save(parser._recordPackages):
#         logger.info("Images saved successfully.")
#     else:
#         logger.error("Failed to save images.")


# # Example usage
# drc_file_path = "/home/hunter/drc_download_platfor/test_drc/record_20250114_150848.drc"
# output_dir = "/home/hunter/drc_download_platfor/saved_images"
# process_drc_file(drc_file_path, output_dir)

import os
import struct
import cv2
import numpy as np

def read_drc_file(drc_file, output_dir):
    if not os.path.exists(drc_file):
        print(f"File not found: {drc_file}")
        return
    
    os.makedirs(output_dir, exist_ok=True)
    
    with open(drc_file, 'rb') as f:
        while True:
            # Read LogHeader (assuming it has 8 bytes: real_len (4 bytes) + log_type (4 bytes))
            header = f.read(8)
            if len(header) < 8:
                break  # End of file
            
            real_len, log_type = struct.unpack('II', header)
            
            # Check if it's an image log type (assuming LogType.Result corresponds to 1)
            if log_type == 1:
                image_data = f.read(real_len)
                
                # Convert to numpy array and decode using OpenCV
                image_np = np.frombuffer(image_data, dtype=np.uint8)
                image = cv2.imdecode(image_np, cv2.IMREAD_COLOR)
                
                if image is not None:
                    output_path = os.path.join(output_dir, f'image_{f.tell()}.png')
                    cv2.imwrite(output_path, image)
                    print(f"Saved: {output_path}")
                else:
                    print("Failed to decode image.")
            else:
                f.read(real_len)  # Skip non-image logs

if __name__ == "__main__":
    drc_file = "/home/hunter/drc_download_platfor/test_drc/record_20250114_150848.drc"  # Replace with your DRC file path
    output_dir = "/home/hunter/drc_download_platfor/saved_images"
    read_drc_file(drc_file, output_dir)

