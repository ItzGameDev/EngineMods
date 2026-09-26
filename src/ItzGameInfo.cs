using BepInEx;
using BepInEx.Configuration;
using UnityEngine;

namespace ItzGame.Mods
{
    // ItzGame Info - harmless demo/utility plugin for the EngineMods catalog.
    // Logs load information to the BepInEx console. No gameplay changes.
    [BepInPlugin(GUID, NAME, VERSION)]
    public class ItzGameInfoPlugin : BaseUnityPlugin
    {
        public const string GUID = "com.itzgame.info";
        public const string NAME = "ItzGame Info";
        public const string VERSION = "1.0.0";

        private void Awake()
        {
            ConfigEntry<string> greeting = Config.Bind("General", "Greeting",
                "ItzGame mod loaded", "Line logged when the plugin starts.");
            Logger.LogInfo(NAME + " " + VERSION + " loaded.");
            Logger.LogInfo(greeting.Value);
            Logger.LogInfo("Unity " + Application.unityVersion + " | " + SystemInfo.operatingSystem);
            Logger.LogInfo("Game data path: " + Application.dataPath);
        }

        private void OnDestroy()
        {
            Logger.LogInfo(NAME + " unloaded.");
        }
    }
}
