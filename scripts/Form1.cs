using static replayer.CarrierMods;
using System.IO;
namespace replayer
{
    public partial class Form1 : Form
    {

        public Form1()
        {
            InitializeComponent();
            this.Text = @"drc_tools";
            _recordDataParser = new RecordDataParser();
        }

        private void OpenFile_Click(object sender, EventArgs e)
        {
            if (openRecordFile.ShowDialog() == DialogResult.OK)
            {
                _recordFileName = openRecordFile.FileName;
                _recordDataParser.ParserPackage(_recordFileName);
            }
        }

        private string? _recordFileName;
        private ModID modId;
        private readonly RecordDataParser _recordDataParser;
        private void saveLogs_Click(object sender, EventArgs e)
        {
            _recordDataParser.ParserMod(ModID.MOD_ID_LOG);
            string log_path = AppDomain.CurrentDomain.SetupInformation.ApplicationBase + "record\\log\\";

            if (!Directory.Exists(log_path))
            {
                Directory.CreateDirectory(log_path);
            }

            var record_name = _recordFileName?.Split("\\");
            string file_name = log_path + record_name?.Last() + ".txt";

            if (!File.Exists(file_name))
            {
                File.Create(file_name).Close();
            }
            // ���ļ�Ŀ¼
            System.Diagnostics.Process.Start(Environment.GetEnvironmentVariable("WINDIR") + @"\\explorer.exe", log_path);
            if (_recordDataParser.SaveLogs(file_name))
            {
                //System.Diagnostics.Process.Start("explorer.exe", log_path);
                //System.Diagnostics.Process.Start(log_path);
                MessageBox.Show(@"log saved!" + file_name);
                //System.Diagnostics.Process.Start(file_name);
            }
        }

        private void button1_Click(object sender, EventArgs e)
        {
            MessageBox.Show(_recordDataParser.SavePic() ? "picture saved!" : "picture save failed!");
        }
    }
}