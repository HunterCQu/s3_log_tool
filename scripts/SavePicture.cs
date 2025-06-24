using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;
using replayer.Helper;
using CV = OpenCvSharp;
using static replayer.CarrierMods;
using Microsoft.VisualBasic.Logging;
using System.Globalization;
using Windows.Devices.Bluetooth.Advertisement;
using System.Text.RegularExpressions;

namespace replayer
{
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Ansi, Pack = 1)]
    public struct PerceiveHead
    {
        public byte SysCount;
        public byte Type;
        public uint Len;
        public UInt64 TimeStamp;
    }
    internal class PerceiveResultParser
    {
        private PerceiveHead _head;
        private readonly IntPtr _headPtr = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(PerceiveHead)));
        private readonly byte[] _perceiveResultData = new byte[1024 * 1024];
        public bool HasNewData { get; private set; } = false;

        public PerceiveHead Head => _head;

        public byte[] PerceiveResultData
        {
            get
            {
                HasNewData = false;
                return _perceiveResultData;
            }
        }
        #region 本地文件测试

#if fasle
    private bool _hasRead = false;
    private readonly byte[] _localDataBuf = new byte[200 * 1024];
    private readonly string _picturePath = System.AppDomain.CurrentDomain.BaseDirectory + @"\map\";
    private int _len = 0;
    public void LoadPicture()
    {
        if (_hasRead) return;
        using var fs = File.OpenRead(_picturePath + "log_to_pc_msg.bin");
        var len = fs.Read(_localDataBuf, 0, Convert.ToInt32(fs.Length));
        _len = len;
        ProcessData(_localDataBuf, 0);
        _hasRead = true;
    }
#endif

        #endregion

        private void ProcessData(byte[] data, int offset, int len)
        {
            // 复制包头
            var head_size = Marshal.SizeOf(typeof(PerceiveHead));
            Marshal.Copy(data, offset, _headPtr, head_size);
            offset += head_size;
            _head = (PerceiveHead)Marshal.PtrToStructure(_headPtr, typeof(PerceiveHead));
            if (_head.Len + head_size > len)
                return;
            //_head.Len = _head.Len - Convert.ToUInt32(head_size); // 计算body长度
            // 复制body
            Array.Copy(data, offset, _perceiveResultData, 0, _head.Len);
            HasNewData = true;
        }

        public void Update(byte[] data, int len)
        {
            ProcessData(data, 0, len);
        }
    }
    internal class SavePicture
    {

        private string? PicturePath
        {
            get
            {
                field ??= PathHelper.GetRecordPath() + "picture\\";
                if (!System.IO.Directory.Exists(field))
                {
                    System.IO.Directory.CreateDirectory(field);
                }
                return field;
            }
        }


        private long _startRealUnixTs = 0;
        private long _startSysTs = 0;
        private readonly PerceiveResultParser _parser = new();
        public string? RecordDir
        {
            get => field;
            set
            {
                field = PicturePath + value;
            
                if (value is null) return;
                const string pattern = @"(\d{8}_\d{6})";
                Match match = Regex.Match(value, pattern);
                string dateStr = "19700101_0000";
                if (match.Success)
                {
                    dateStr = match.Value;
                }
                DateTime dateTime = DateTime.ParseExact(dateStr, "yyyyMMdd_HHmmss", CultureInfo.InvariantCulture);
                _startRealUnixTs = ((DateTimeOffset)dateTime).ToUnixTimeMilliseconds();
                if (!Directory.Exists(field)) Directory.CreateDirectory(field);
            }
        }
        private int CalEdgeCnt(int num)
        {
            for (int i = 1; i <= num; i++)
            {
                if (i * i >= num)
                    return i;
            }
            return 0;
        }
        private CV.Mat ReshapeMat(CV.Mat input)
        {
            var (w, h) = (input.Width, input.Height);
            int single_w = 320, single_h = h;
            var edge_num = CalEdgeCnt(w / single_w);
            CV.Mat ret = CV.Mat.Zeros(single_h * edge_num, single_w * edge_num, input.Type());
            //Log.Debug($"ret height{ret.Size().Height} wight{ret.Size().Width}");
            for (int i = 0; i < w / single_w; i++)
            {
                var (dest_i, dest_j) = (i / edge_num, i % edge_num);
                var dest = new CV.Rect(dest_j * single_w, dest_i * single_h, single_w, single_h);
                //var dest = ret.SubMat();
                //var source = input.SubMat(0, h , i * h, (i + 1) * h );
                var source_rec = new CV.Rect(i * single_w, 0, single_w, h);
                input[source_rec].CopyTo(ret[dest]);
            }
            return ret;
        }

        public bool Save(List<RecordDataParser.RecordPackage> records)
        {
            if (RecordDir is null) return false;
            _startSysTs = 0;
            foreach (var record in records)
            {
                _parser.Update(record.Data, (int)record.RealLen);
                if (!_parser.HasNewData) continue;
                if (_parser.Head.Type > 30) continue;
                if (_startSysTs == 0)
                    _startSysTs = (long)_parser.Head.TimeStamp / 1000;
                var file_name = RecordDir + "\\" + TimeHelper.GetTimeStr(_startRealUnixTs + (long)_parser.Head.TimeStamp / 1000 - _startSysTs)  + ".png";
                PathHelper.GetUniqueName(file_name);
                var img_data = new byte[_parser.Head.Len];
                Array.Copy(_parser.PerceiveResultData, img_data, _parser.Head.Len);
                var image_mat = CV.Cv2.ImDecode(img_data, CV.ImreadModes.Color);
                if (image_mat.Empty())
                {
                    continue;
                }
                var new_mat = ReshapeMat(image_mat);
                CV.Cv2.ImWrite(file_name, new_mat);

                //if (File.Exists(file_name)) continue;
                //File.Create(file_name).Close();
            }

            ShowDir();
            return true;
        }

        public void ShowDir()
        {
            System.Diagnostics.Process.Start(Environment.GetEnvironmentVariable("WINDIR") + @"\\explorer.exe", PicturePath);
        }

    }
}
