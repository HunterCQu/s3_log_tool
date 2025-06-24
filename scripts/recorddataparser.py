import os
import struct
import csv
from enum import IntEnum
from collections import namedtuple
from typing import List, Dict, Tuple

class ModID(IntEnum):
    MOD_ID_IMU_FB = 0
    MOD_ID_CARRIER_POS_FB = 1
    MOD_ID_WIRE_POS_FB = 2
    MOD_ID_WIRE_POSBACK_FB = 3
    MOD_ID_BASE_INFO_FB = 4
    MOD_ID_WIRE_PATROL_FB = 5
    MOD_ID_WHEEL_LEFT_FB = 6
    MOD_ID_WHEEL_RIGHT_FB = 7
    MOD_ID_MOTOR_CUTTER_FB = 8
    MOD_ID_MOTOR_LIFT_FB = 9
    MOD_ID_CUTTER_LIFT_FB = 10
    MOD_ID_BATTERY_FB = 11
    MOD_ID_RAINDET_FB = 12
    MOD_ID_LOG = 13
    MOD_ID_COLLISION_FB = 14
    MOD_ID_STOP_KEY_FB = 15
    MOD_ID_PICK_UP_FB = 16
    MOD_ID_INFO_FB = 17
    MOD_ID_ERROR_STATE_FD = 18
    MOD_ID_KEY_PIN_FB = 19
    MOD_ID_DEBUG_INT32_FB = 20
    MOD_ID_DEBUG_FLOAT_FB = 21
    MOD_ID_MS_STATUS_FB = 22
    MOD_ID_MOWER_POSE3D_FB = 23

class LogType(IntEnum):
    Text = 0
    Result = 1

class ModStruct:
    def __init__(self, mod_id: ModID, struct_type, description: str):
        self.mod_id = mod_id
        self.struct_type = struct_type
        self.description = description

class RecordPackage:
    def __init__(self, timestamp: int, data: bytes, real_len: int):
        self.timestamp = timestamp
        self.data = data
        self.real_len = real_len

class RecordDataParser:
    def __init__(self):
        self.mModProperties = [
            ModStruct(ModID.MOD_ID_IMU_FB, None, "IMU信息"),
            # Add all other ModStruct entries here
        ]
        self.mModPtrDictionary = {mod.mod_id: mod for mod in self.mModProperties}
        self.mLogLines: List[str] = []
        self._recordPackages: List[RecordPackage] = []
        self._imagePackages: List[RecordPackage] = []
        self._modStructs: List[ModStruct] = []
        self._mod_backpossensorStructs: List = []
        self._mod_timestamps: List[int] = []
        self._mod_lichengji: List = []
        self._mod_backpos: List = []
        self._timestamps: List[int] = []

    def parse_package(self, file_name: str) -> bool:
        if not os.path.exists(file_name):
            return False
        
        self._recordPackages.clear()
        header_size = 24  # Adjust based on actual LogHeader size
        robot_header_size = 16  # Adjust based on RobotProtocolHeader
        
        with open(file_name, 'rb') as fs:
            while True:
                head_buf = fs.read(header_size)
                if not head_buf:
                    break
                
                # Unpack LogHeader (adjust format string based on actual structure)
                # Example: log_head = struct.unpack('<IQQ', head_buf)
                # real_len, log_type, time_stamp = log_head
                
                # Read package data
                mod_id = fs.read(1)
                mod_offset = fs.read(1)
                mod_len_bytes = fs.read(4)
                mod_len = struct.unpack('<I', mod_len_bytes)[0]
                
                data = head_buf + mod_id + mod_offset + mod_len_bytes + fs.read(mod_len)
                self._recordPackages.append(RecordPackage(0, data, mod_len))  # Update timestamp
        
        return True

    def parse_mod(self, mod_id: ModID) -> bool:
        self._modStructs.clear()
        self.mLogLines.clear()
        
        for package in self._recordPackages:
            data = package.data
            offset = 0  # Skip RobotProtocolHeader
            while offset < len(data):
                current_mod_id = ModID(data[offset])
                offset += 1
                mod_offset = data[offset]
                offset += 1
                mod_len = struct.unpack('<I', data[offset:offset+4])[0]
                offset += 4
                
                if current_mod_id == mod_id:
                    mod_data = data[offset:offset+mod_len]
                    # Process mod_data based on struct_type
                    if mod_id == ModID.MOD_ID_LOG:
                        log_str = mod_data.split(b'\x00')[0].decode('ascii')
                        self.mLogLines.append(log_str)
                    
                    # Create ModStruct instance and add to _modStructs
                
                offset += mod_len
        
        return True

    def save_logs(self, file_name: str) -> bool:
        with open(file_name, 'w', encoding='utf-8') as f:
            for line in self.mLogLines:
                f.write(line + '\n')
        return True

    def save_sensordata(self, file_name: str) -> bool:
        if not self._modStructs:
            return False
        
        with open(file_name, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            # Write header
            writer.writerow(['timestamp', 'field1', 'field2'])  # Add actual fields
            
            # Write data rows
            for mod in self._modStructs:
                # Extract fields from mod data
                row = [mod.timestamp]  # Add actual data fields
                writer.writerow(row)
        
        return True

# Example usage
parser = RecordDataParser()
parser.parse_package('data.bin')
parser.parse_mod(ModID.MOD_ID_LOG)
parser.save_logs('output.log')