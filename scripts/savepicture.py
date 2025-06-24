import os
import re
import time
import numpy as np
import cv2
from datetime import datetime
from pathlib import Path


class PerceiveHead:
    def __init__(self, sys_count, type_, length, timestamp):
        self.sys_count = sys_count
        self.type = type_
        self.length = length
        self.timestamp = timestamp


class PerceiveResultParser:
    def __init__(self):
        self.head = None
        self.perceive_result_data = bytearray(1024 * 1024)
        self.has_new_data = False

    def process_data(self, data, offset, length):
        head_size = 16  # Size of PerceiveHead structure
        # Read header
        self.head = PerceiveHead(
            data[offset], data[offset + 1], int.from_bytes(data[offset + 2:offset + 6], byteorder='little'),
            int.from_bytes(data[offset + 6:offset + 14], byteorder='little')
        )
        offset += head_size

        if self.head.length + head_size > length:
            return

        # Copy body data
        self.perceive_result_data[:self.head.length] = data[offset:offset + self.head.length]
        self.has_new_data = True

    def update(self, data, length):
        self.process_data(data, 0, length)

    @property
    def perceive_result_data(self):
        self.has_new_data = False
        return self._perceive_result_data

    @perceive_result_data.setter
    def perceive_result_data(self, value):
        self._perceive_result_data = value


class SavePicture:
    def __init__(self):
        self._start_real_unix_ts = 0
        self._start_sys_ts = 0
        self._parser = PerceiveResultParser()
        self.record_dir = None

    @property
    def picture_path(self):
        path = str(Path(__file__).parent / "map" / "picture")
        if not os.path.exists(path):
            os.makedirs(path)
        return path

    @property
    def record_dir(self):
        return self._record_dir

    @record_dir.setter
    def record_dir(self, value):
        self._record_dir = self.picture_path + value
        if value is None:
            return
        match = re.search(r"(\d{8}_\d{6})", value)
        date_str = "19700101_0000"
        if match:
            date_str = match.group(1)
        date_time = datetime.strptime(date_str, "%Y%m%d_%H%M%S")
        self._start_real_unix_ts = int(time.mktime(date_time.timetuple()) * 1000)
        if not os.path.exists(self._record_dir):
            os.makedirs(self._record_dir)

    def cal_edge_cnt(self, num):
        for i in range(1, num + 1):
            if i * i >= num:
                return i
        return 0

    def reshape_mat(self, input_mat):
        w, h = input_mat.shape[1], input_mat.shape[0]
        single_w, single_h = 320, h
        edge_num = self.cal_edge_cnt(w // single_w)
        ret = np.zeros((single_h * edge_num, single_w * edge_num, input_mat.shape[2]), dtype=np.uint8)

        for i in range(w // single_w):
            dest_i, dest_j = i // edge_num, i % edge_num
            dest = ret[dest_i * single_h:(dest_i + 1) * single_h, dest_j * single_w:(dest_j + 1) * single_w]
            source_rec = input_mat[0:h, i * single_w:(i + 1) * single_w]
            dest[:] = source_rec
        return ret

    def save(self, records):
        if self.record_dir is None:
            return False

        self._start_sys_ts = 0
        for record in records:
            self._parser.update(record.data, record.real_len)
            if not self._parser.has_new_data:
                continue

            if self._parser.head.type > 30:
                continue

            if self._start_sys_ts == 0:
                self._start_sys_ts = self._parser.head.timestamp // 1000

            file_name = os.path.join(self.record_dir, f"{self._start_real_unix_ts + self._parser.head.timestamp // 1000 - self._start_sys_ts}.png")
            img_data = self._parser.perceive_result_data[:self._parser.head.length]

            image_mat = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_COLOR)
            if image_mat is None or image_mat.size == 0:
                continue

            new_mat = self.reshape_mat(image_mat)
            cv2.imwrite(file_name, new_mat)

        self.show_dir()
        return True

    def show_dir(self):
        os.startfile(self.picture_path)


# Helper classes for the record and path handling
class RecordDataParser:
    class RecordPackage:
        def __init__(self, data, real_len):
            self.data = data
            self.real_len = real_len


class PathHelper:
    @staticmethod
    def get_record_path():
        return str(Path(__file__).parent) + "/map/"

    @staticmethod
    def get_unique_name(file_name):
        if os.path.exists(file_name):
            base_name, ext = os.path.splitext(file_name)
            counter = 1
            while os.path.exists(f"{base_name}_{counter}{ext}"):
                counter += 1
            return f"{base_name}_{counter}{ext}"
        return file_name


class TimeHelper:
    @staticmethod
    def get_time_str(timestamp):
        return datetime.utcfromtimestamp(timestamp / 1000).strftime('%Y%m%d_%H%M%S')
