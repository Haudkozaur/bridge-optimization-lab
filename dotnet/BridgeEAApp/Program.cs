using BridgeEAApp.Optimization;
using BridgeEAApp.Reporting;
using BridgeEAApp.Surrogate;

var root = Path.GetFullPath(
    Path.Combine(
        AppDomain.CurrentDomain.BaseDirectory,
        "..",
        "..",
        "..",
        ".."));

var modelsDir = args.Length > 0
    ? args[0]
    : @"D:\Doktorat\bridge-optimization-lab\dotnet\models_multi_span\run_20260710_011914";

if (!Directory.Exists(modelsDir))
{
    throw new DirectoryNotFoundException($"Models directory not found: {modelsDir}");
}

var zipCount = Directory.GetFiles(modelsDir, "*.zip").Length;

Console.WriteLine($"Manual models dir: {modelsDir}");
Console.WriteLine($"Zip models found:  {zipCount}");

if (zipCount == 0)
{
    throw new Exception($"No .zip ML models found in manual models directory: {modelsDir}");
}

Console.WriteLine("MULTI-SPAN BRIDGE EA APP");
Console.WriteLine($"Root:        {root}");
Console.WriteLine($"Models dir:  {modelsDir}");
Console.WriteLine();

var fitnessEvaluator =
    SurrogateModelFactory.CreateDefault(modelsDir);

var optimizer = new RandomSearchOptimizer();

var optimizationMode =
    OptimizationMode.MutationWithRandomRestart;

var template = CreateTemplateCandidate();

Console.WriteLine("Template candidate:");
Console.WriteLine($"N spans:     {template.NSpans}");
Console.WriteLine($"Total L:     {template.TotalSpanLengthM:F3} m");
Console.WriteLine($"Active CP:   {template.ActiveTendonControlPointCount}");
Console.WriteLine();

var best = optimizer.Optimize(
    template,
    iterations: 100_000_0,
    patience: 100_000,
    mode: optimizationMode,
    fitnessEvaluator);

var bestResult =
    fitnessEvaluator.EvaluateDetailed(best);

ConsoleResultPrinter.PrintBestCandidate(
    best,
    bestResult);

static BridgeCandidate CreateTemplateCandidate()
{
    var candidate = new BridgeCandidate
    {
        NSpans = 3,

        SpanLengthsM = new float[]
        {
            25.0f, 25.0f, 25.0f, 0.0f,
            0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f
        },

        BeamDivisions = new int[]
        {
            100, 100, 100, 0,
            0, 0, 0, 0, 0, 0
        },

        UdlValuesKnPerM = new float[]
        {
            10.0f, 10.0f, 10.0f, 0.0f,
            0.0f, 0.0f, 0.0f, 0.0f, 0.0f, 0.0f
        },

        BeamHeightM = 1.2f,
        BeamWidthM = 0.5f,
        TendonCoverM = 0.05f,

        NTendons = 3,
        TendonForceKn = 220.0f,
        TendonAreaMm2 = 150.0f
    };

    for (var i = 0; i < BridgeCandidate.MaxTendonControlPoints; i++)
        candidate.TendonEccControlPointsM[i] = 0.0f;

    return candidate;
}

static string GetLatestRunDirectory(string modelsRoot)
{
    if (!Directory.Exists(modelsRoot))
        throw new DirectoryNotFoundException($"Models root not found: {modelsRoot}");

    var latest = Directory
        .GetDirectories(modelsRoot, "run_*")
        .OrderByDescending(x => x)
        .FirstOrDefault();

    if (latest is null)
        throw new Exception($"No run_* directory found in: {modelsRoot}");

    return latest;
}