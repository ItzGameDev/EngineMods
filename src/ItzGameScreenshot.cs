using System;
using System.IO;
using BepInEx;
using UnityEngine;

namespace ItzGame.Mods
{
    // ItzGame Screenshot - quality-of-life plugin for the EngineMods catalog.
    // Press F9 to save a PNG into <game>/ItzGameScreenshots/. No gameplay changes.
    [BepInPlugin(GUID, NAME, VERSION)]
    public class ItzGameScreenshotPlugin : BaseUnityPlugin
    {
        public const string GUID = "com.itzgame.screenshot";
        public const string NAME = "ItzGame Screenshot";
        public const string VERSION = "1.0.0";

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.F9))
                Capture();
        }

        private void Capture()
        {
            try
            {
                string dir = Path.Combine(Application.dataPath, "..", "ItzGameScreenshots");
                Directory.CreateDirectory(dir);
                string file = Path.Combine(dir, "gt-" + DateTime.Now.ToString("yyyyMMdd-HHmmss") + ".png");
                ScreenCapture.CaptureScreenshot(file);
                Logger.LogInfo("Screenshot requested: " + file);
            }
            catch (Exception e)
            {
                Logger.LogWarning("Screenshot failed: " + e.Message);
            }
        }
    }
}
