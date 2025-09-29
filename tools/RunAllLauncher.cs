using System;
using System.Diagnostics;
using System.IO;

namespace AutomatoLaunchers
{
    internal static class RunAllLauncher
    {
        [STAThread]
        private static void Main()
        {
            try
            {
                string exeDir = AppDomain.CurrentDomain.BaseDirectory;
                string script = Path.Combine(exeDir, "run_all.ps1");
                if (!File.Exists(script))
                {
                    Console.Error.WriteLine("Script não encontrado: " + script);
                    return;
                }

                var psi = new ProcessStartInfo();
                psi.FileName = "powershell.exe";
                psi.Arguments = "-NoProfile -ExecutionPolicy Bypass -File \"" + script + "\"";
                psi.UseShellExecute = true;
                psi.Verb = "runas";
                psi.WorkingDirectory = exeDir;

                Process.Start(psi);
            }
            catch (System.ComponentModel.Win32Exception ex)
            {
                // 1223: The operation was canceled by the user (UAC cancel)
                if (ex.NativeErrorCode != 1223)
                {
                    Console.Error.WriteLine("Falha ao iniciar PowerShell elevado: " + ex.Message);
                }
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine("Erro: " + ex.Message);
            }
        }
    }
}


