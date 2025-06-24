using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using static replayer.CarrierMods;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.IO;


namespace replayer
{
    internal class RecordDataParser
    {
        //AreaCal area_cal
        //{
        //    Scale = 0.2;
        //};
        ModStruct[] mModProperties = {
                new ModStruct(ModID.MOD_ID_IMU_FB, typeof(ModImuFb), "IMU信息"),
                new ModStruct(ModID.MOD_ID_CARRIER_POS_FB, typeof(ModChassisPosFb), "底盘信息"),
                new ModStruct(ModID.MOD_ID_WIRE_POS_FB, typeof(ModWirePosFb), "电线定位信息"),
                new ModStruct(ModID.MOD_ID_WIRE_POSBACK_FB, typeof(ModWirePosFb), "电线定位信息back"),
                new ModStruct(ModID.MOD_ID_BASE_INFO_FB, typeof(ModBaseInfoFb), "基站模块的信息"),

                new ModStruct(ModID.MOD_ID_WIRE_PATROL_FB, typeof(ModWirePatrolFb), "电线方向信息"),
                new ModStruct(ModID.MOD_ID_WHEEL_LEFT_FB, typeof(ModMotorFb), "左轮电机"),
                new ModStruct(ModID.MOD_ID_WHEEL_RIGHT_FB, typeof(ModMotorFb), "右轮电机"),
                new ModStruct(ModID.MOD_ID_MOTOR_CUTTER_FB, typeof(ModMotorFb), "割草电机"),
                new ModStruct(ModID.MOD_ID_MOTOR_LIFT_FB, typeof(ModMotorFb), "抬升电机"),
                new ModStruct(ModID.MOD_ID_CUTTER_LIFT_FB, typeof(ModCutterLiftFb), "抬升模块"),
                new ModStruct(ModID.MOD_ID_BATTERY_FB, typeof(ModBatteryFb), "电池信息"),
                new ModStruct(ModID.MOD_ID_RAINDET_FB, typeof(ModRaindetFb), "雨量信息"),
                new ModStruct(ModID.MOD_ID_LOG, typeof(ModLog), "日志信息"),
                new ModStruct(ModID.MOD_ID_COLLISION_FB, typeof(ModCollisionFb), "碰撞模块"),
                new ModStruct(ModID.MOD_ID_STOP_KEY_FB, typeof(ModStopKeyFb), "急停模块"),
                new ModStruct(ModID.MOD_ID_PICK_UP_FB, typeof(ModPickUpFb), "抱起模块"),
                new ModStruct(ModID.MOD_ID_INFO_FB, typeof(ModSysInfoFb), "系统信息"),
                new ModStruct(ModID.MOD_ID_ERROR_STATE_FD, typeof(ModErrorstateFb), "报错信息"),
                new ModStruct(ModID.MOD_ID_KEY_PIN_FB, typeof(ModKeyPinFb), "按键和pin码"),
                new ModStruct(ModID.MOD_ID_DEBUG_INT32_FB, typeof(ModDebugInt32Fb), "Int32调试数据模块"),
                new ModStruct(ModID.MOD_ID_DEBUG_FLOAT_FB, typeof(ModDebugFloatFb), "Float调试数据模块"),
                new ModStruct(ModID.MOD_ID_MS_STATUS_FB, typeof(ModMsStatusFb), "割草机状态"),
                new ModStruct(ModID.MOD_ID_MOWER_POSE3D_FB, typeof(MowerPose3D), "坐标")
            };
        Dictionary<ModID, ModStruct> mModPtrDictionary = new Dictionary<ModID, ModStruct>();
        List<string> mLogLines = new List<string>();
        private IntPtr _headerPtr = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(LogHeader)));
        public RecordDataParser()
        {

            foreach (var ms in mModProperties)
            {
                mModPtrDictionary.Add(ms.GetModID(), ms);
            }
        }

        public void save_timestamps()
        {
            string file_name = "timestamp.txt";
            string record_path = AppDomain.CurrentDomain.SetupInformation.ApplicationBase + "record\\";
            file_name = record_path + file_name;

            if (!File.Exists(file_name))
            {
                File.Create(file_name).Close();
            }
            FileInfo save_file = new FileInfo(file_name);
            var sw = save_file.CreateText();
            foreach (var ts in _timestamps)
            {
                string line = ts.ToString();
                sw.WriteLine(line);
            }
            sw.Close();

        }
        public bool ParserPackage(string file_name)
        {
            
            if(!File.Exists(file_name)) { return false;}
            _recordPackages.Clear();
            FileStream fs = new FileStream(file_name, FileMode.Open);
            byte[] head_buf = new byte[Marshal.SizeOf(typeof(LogHeader))];
            Int64 cur = 0;
            Console.WriteLine("测试文件! ");
            while (cur < fs.Length)
            {
                var rx_len = fs.Read(head_buf, 0, head_buf.Length);
                cur += rx_len;
                if (rx_len != head_buf.Length)
                {
                    fs.Close();
                    MessageBox.Show(@"数据异常！");
                    return false;
                }
                
                Marshal.Copy(head_buf, 0,  _headerPtr, head_buf.Length);
                LogHeader? log_head = Marshal.PtrToStructure(_headerPtr, typeof(LogHeader)) as LogHeader;
                //unsafe
                //{
                //    log_head = *(LogHeader*)Marshal.UnsafeAddrOfPinnedArrayElement(head_buf, 0);
                //}
                if (log_head == null)
                {
                    fs.Close();
                    MessageBox.Show("数据错误");
                    return false;
                }

                var real_len = log_head.real_len;
                var log_type = log_head.log_type;
                // 读取数据
                var package_data = new byte[Marshal.SizeOf(typeof(RobotProtocolHeader)) +
                                            Marshal.SizeOf(typeof(SmallPackHead2)) + real_len + 1];
                // 拷贝robot header
                var offset = 0;
                Array.Copy(head_buf, offset, package_data, offset, Marshal.SizeOf(typeof(RobotProtocolHeader)));
                offset += Marshal.SizeOf(typeof(RobotProtocolHeader));
                // 拷贝 small header
                package_data[offset++] = (byte)ModID.MOD_ID_LOG; // mod id
                package_data[offset++] = (byte)0; // mod offset
                var mod_len_bytes = BitConverter.GetBytes(real_len + 1);
                Array.Copy(mod_len_bytes, 0, package_data, offset, Marshal.SizeOf(typeof(int)));
                offset += Marshal.SizeOf(typeof(int));
                // 读取数据
                rx_len = fs.Read(package_data, offset, real_len);
                cur += rx_len;
                if (rx_len != real_len) {
                    fs.Close();
                    MessageBox.Show(@"数据异常！");
                    return false;
                }
                if (log_type is LogType.Text )
                    _recordPackages.Add(new RecordPackage(log_head.robot_header.time_stamp, package_data, real_len));
                if (log_type is LogType.Result)
                {
                    var image_data = new byte[real_len];
                    Array.Copy(package_data, offset, image_data, 0, real_len);
                    _imagePackages.Add(new RecordPackage(log_head.robot_header.time_stamp, image_data, real_len));
                }
            }
            fs.Close();
            if (_recordPackages.Count == 0)
            {
                MessageBox.Show(@"解析不到数据！");
                return false;
            }
            else
            {
                //save_timestamps();
                MessageBox.Show(@"解析成功");
                _savePicture.RecordDir = Path.GetFileNameWithoutExtension(file_name);
            }
            return true;
        }

        public bool ParserMod(ModID id)
        {
            _modStructs.Clear();
            mLogLines.Clear();
            _mod_backpossensorStructs.Clear();
            Console.WriteLine("21212!");
            Int32 cur_pos = 0;

            foreach (var package in _recordPackages)
            {
                int cur = 0;
                var data = package.Data;
                Int64 ts = package.TimeStamp;
                int rx_len = data.Length;
                int head_len = Marshal.SizeOf(typeof(RobotProtocolHeader));
                cur += head_len;

                while (cur < rx_len - 2)
                {
                    ModID mod_id = (ModID)data[cur++];
                    int mod_offset = (int)data[cur++];
                    int mod_len = BitConverter.ToInt32(data, cur);
                    cur += Marshal.SizeOf(typeof(int));
                    
                    Console.WriteLine("ts:{0}", cur_pos);
                    if (mod_id == id)
                    {
                        _mod_timestamps.Add(ts);
                        var ms = mModPtrDictionary[mod_id];
                        ModStruct mod = new ModStruct(ms.GetModID(), ms.GetStructType(), ms.ToString());
                        mod.Update(data, cur, mod_offset, mod_len);
                        if (mod_id == ModID.MOD_ID_LOG)
                        {
                            byte[] log_bytes = new byte[mod_len];
                            Array.Copy(data, cur, log_bytes, 0,  mod_len);
                            if (log_bytes != null)
                            {
                                string log_str = "";
                                string log_str_new = System.Text.Encoding.ASCII.GetString(log_bytes);

                                int part = log_str_new.IndexOf('\0'); // 第一次出现的位置
                                if(part>0)
                                {
                                    log_str += log_str_new.Substring(0, part);
                                    mLogLines.Add(log_str);
                                }
                                
                                //log_str.TrimEnd('\0');
                                //log_str.TrimEnd('\n');
                                //log_str.TrimEnd('\r');
                                
                            }
                        }
                        _modStructs.Add(mod);
                    }

                    cur += mod_len;
                } 
            }

            return true;
        }

        public bool SaveLogs(string file_name)
        {
            FileInfo log_file = new FileInfo(file_name);
            var sw = log_file.CreateText();
            foreach (var line in mLogLines)
            {
                sw.WriteLine(line);
            }
            sw.Close();
            return true;
        }


        public bool SaveSensordata(string file_name)
        {
            if (_modStructs.Count == 0)
            {
                Console.WriteLine(@"mod structs is empty!");
                return false;
            }

            FileInfo save_file = new FileInfo(file_name);
            var sw = save_file.CreateText();
            
            var type = _modStructs[0].GetStructType();
            var fields = type.GetFields();

        
            string head = "";
            head = head + "tickms" + ',';
            head = head + "lichengjijifen" + ',';
            foreach (var field in fields)
            {
                head = head + field.Name + ',';
            }
            head = head + "backpos_wirepos" + ',';
            head = head + "backpos_confidence" + ',';
            head = head + "backpos_cons_ns" + ',';
            head = head + "backpos_cons_std" + ',';
            head = head + "backpos_cons_Aa" + ',';
            head = head + "backpos_cons_piancha" + ',';

            head.TrimEnd(',');
            
            sw.WriteLine(head);

            int i = 0;
            foreach (var ms in _modStructs)
            {
                RecordChassisPos curpos = _mod_lichengji[i];
                ModWirePosFb newposbacksensor = _mod_backpos[i];
                i++;

                var mod = ms.GetNewStruct();
         
                string line = "";
                line = line + curpos.TimeStamp.ToString() + ",";
                line = line + curpos.Data.ToString() + ",";

                
                foreach (var field in fields)
                {
                    if (field.Name == "accel_z" && field.GetValue(mod).ToString() == "0")
                    {

                    }
                    line = line + field.GetValue(mod).ToString() + ",";
                }
                
       
                line = line + newposbacksensor.wirepos.ToString() + ",";
                line = line + newposbacksensor.confidence.ToString() + ",";
                line = line + newposbacksensor.cons_A1.ToString() + ",";
                line = line + newposbacksensor.cons_A2.ToString() + ",";
                line = line + newposbacksensor.cons_A3.ToString() + ",";
                line = line + newposbacksensor.cons_A4.ToString() + ",";
              

                line.TrimEnd(',');
                sw.WriteLine(line);
            }
            sw.Close();
            return true;
        }
		
		
        public void SaveMods(string file_name)
        {
            if (_modStructs.Count == 0)
            {
                Console.WriteLine(@"mod structs is empty!");
                return;
            }

            FileInfo save_file = new FileInfo(file_name);
            var sw = save_file.CreateText();
            
            var type = _modStructs[0].GetStructType();
            var fields = type.GetFields();
            string head = "";
            foreach (var field in fields)
            {
                head = head + field.Name + ',';
            }

            head.TrimEnd(',');
            
            sw.WriteLine(head);
            
            
            foreach (var ms in _modStructs)
            {
                
                var mod = ms.GetNewStruct();

                string line = "";
                foreach (var field in fields)
                {
                    if (field.Name == "accel_z" && field.GetValue(mod).ToString() == "0")
                    {

                    }

                    line = line + field.GetValue(mod).ToString() + ",";
                }

                line.TrimEnd(',');
                sw.WriteLine(line);
            }
            sw.Close();
        }
        public class RecordPackage
        {
            public RecordPackage(Int64 ts, byte[] data, long realLen)
            {
                TimeStamp = ts;
                this.Data = data;
                RealLen = realLen;

            }

            public Int64 TimeStamp;
            public byte[] Data;
            public Int64 RealLen;

        }

        class RecordChassisPos
        {
            public RecordChassisPos(Int64 ts, Int32 data)
            {
                TimeStamp = ts;
                this.Data = data;
            }

            public Int64 TimeStamp;
            public Int32 Data;

        }

        public bool SavePic()
        {
            return _savePicture.Save(_imagePackages);
        }
        private List<RecordPackage> _recordPackages = new List<RecordPackage>();
        private List<RecordPackage> _imagePackages = new();
        private SavePicture _savePicture = new();
        private List<ModStruct> _modStructs = new List<ModStruct>();
        private List<ModStruct> _mod_backpossensorStructs = new List<ModStruct>();
        private List<Int64> _mod_timestamps = new List<Int64>();
        private List<RecordChassisPos> _mod_lichengji = new List<RecordChassisPos>();

        private List<ModWirePosFb> _mod_backpos = new List<ModWirePosFb>();
        
        private List<uint> _timestamps = new List<uint>();
    }
}
