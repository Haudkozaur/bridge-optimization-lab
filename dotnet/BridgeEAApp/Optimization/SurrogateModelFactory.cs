using BridgeEAApp.Optimization;

namespace BridgeEAApp.Surrogate;

internal static class SurrogateModelFactory
{
    public static BridgeFitnessEvaluator CreateDefault(string modelsDirectory)
    {
        if (!Directory.Exists(modelsDirectory))
            throw new DirectoryNotFoundException($"Models directory not found: {modelsDirectory}");

        var modelFiles = Directory
            .GetFiles(modelsDirectory, "*.zip")
            .OrderBy(x => x)
            .ToArray();

        if (modelFiles.Length == 0)
            throw new Exception($"No .zip ML models found in: {modelsDirectory}");

        var models = new Dictionary<string, MlSurrogateModel>();

        foreach (var modelFile in modelFiles)
        {
            var targetName = GetTargetName(modelFile);

            if (models.ContainsKey(targetName))
                throw new Exception($"Duplicate model target name: {targetName}");

            models[targetName] = new MlSurrogateModel(
                targetName,
                modelFile);
        }

        Console.WriteLine($"Loaded ML models: {models.Count}");
        Console.WriteLine($"Models directory: {modelsDirectory}");
        Console.WriteLine();

        return new BridgeFitnessEvaluator(models);
    }

    private static string GetTargetName(string modelPath)
    {
        var name = Path.GetFileNameWithoutExtension(modelPath);

        if (name.EndsWith("_LightGbm", StringComparison.OrdinalIgnoreCase))
            return name[..^"_LightGbm".Length];

        if (name.EndsWith("_FastTree", StringComparison.OrdinalIgnoreCase))
            return name[..^"_FastTree".Length];

        return name;
    }
}