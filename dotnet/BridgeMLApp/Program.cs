// using BridgeMLApp.Data;
// using BridgeMLApp.Experiments;
// using BridgeMLApp.ML;
// using Microsoft.ML;

// // ============================================================
// // MULTI-SPAN ML TRAINING ENTRY POINT
// // ============================================================
// // How to run:
// //   1) Put multi_span_ml_ready_solver.csv next to BridgeMLApp.csproj
// //      OR next to the .sln
// //      OR pass path explicitly:
// //          dotnet run -- "C:\path\to\multi_span_ml_ready_solver.csv"
// //
// // This Program.cs uses the multi-span pipeline:
// //   MultiSpanFeatureBuilder + MultiSpanCsvBeamDataLoader + MultiSpanExperimentCatalog
// // ============================================================

// var csvPath = ResolveCsvPath(args);
// var modelOutputDirectory = ResolveOutputDirectory("models_multi_span");

// var saveBestModel = true;
// var printFeatureNames = false;
// var printRandomSamples = false;
// var randomSampleCount = 3;

// // First run only smoke tests. When it works, replace with:
// // var selectedExperiments = MultiSpanExperimentCatalog.AllBasicTotalExperiments().ToList();
// // var selectedExperiments = MultiSpanExperimentCatalog.SmokeTests().ToList();
// var selectedExperiments = MultiSpanExperimentCatalog.AllTotalExperiments().ToList();

// var selectedModels = new[]
// {
//     RegressionModelType.LightGbm,
//     RegressionModelType.FastTree,
//     RegressionModelType.FastForest
// };

// var mlContext = new MLContext(seed: 1);

// var featureBuilder = new MultiSpanFeatureBuilder();
// var loader = new MultiSpanCsvBeamDataLoader(mlContext);
// var comparer = new ModelComparer(mlContext);
// var trainingService = new ModelTrainingService(mlContext);

// Console.WriteLine("==================================================");
// Console.WriteLine("MULTI-SPAN BEAM ML TRAINING");
// Console.WriteLine("==================================================");
// Console.WriteLine($"Base directory:  {AppContext.BaseDirectory}");
// Console.WriteLine($"CSV:             {csvPath}");
// Console.WriteLine($"Models output:   {modelOutputDirectory}");
// Console.WriteLine($"Feature count:   {featureBuilder.FeatureCount}");
// Console.WriteLine($"Experiments:     {selectedExperiments.Count}");
// Console.WriteLine();

// Directory.CreateDirectory(modelOutputDirectory);

// foreach (var experiment in selectedExperiments)
// {
//     Console.WriteLine();
//     Console.WriteLine("==================================================");
//     Console.WriteLine($"EXPERIMENT: {experiment.Name}");
//     Console.WriteLine($"TARGET:     {experiment.TargetColumn}");
//     Console.WriteLine("==================================================");

//     // Existing debug/reporting methods expect FeatureColumns to contain feature names.
//     // For multi-span, names come from the feature builder, not from the experiment catalog.
//     experiment.FeatureColumns = featureBuilder.FeatureNames.ToArray();

//     if (printFeatureNames)
//     {
//         Console.WriteLine("Features:");
//         foreach (var featureName in experiment.FeatureColumns)
//             Console.WriteLine($"- {featureName}");
//         Console.WriteLine();
//     }

//     try
//     {
//         var data = loader.Load(
//             filePath: csvPath,
//             targetColumn: experiment.TargetColumn,
//             featureBuilder: featureBuilder);

//         var rows = loader.LastLoadedRecords;

//         PrintLabelStats(rows);

//         if (printRandomSamples)
//             PrintRandomSamples(rows, experiment.FeatureColumns, randomSampleCount);

//         var numberOfFolds = Math.Min(5, rows.Count);

//         if (numberOfFolds < 2)
//         {
//             Console.WriteLine("Skipping cross-validation and training: too few rows.");
//             continue;
//         }

//         var results = comparer.CompareWithCrossValidation(
//             data: data,
//             numberOfFolds: numberOfFolds,
//             selectedModels: selectedModels);

//         PrintRanking(results, numberOfFolds);

//         if (!saveBestModel || results.Count == 0)
//             continue;

//         if (!Enum.TryParse<RegressionModelType>(results.First().ModelName, out var bestModelType))
//         {
//             Console.WriteLine($"Could not parse best model type: {results.First().ModelName}");
//             continue;
//         }

//         var savedModelPath = trainingService.TrainAndSave(
//             data: data,
//             experiment: experiment,
//             modelType: bestModelType,
//             outputDirectory: modelOutputDirectory);

//         Console.WriteLine();
//         Console.WriteLine($"Saved best model: {savedModelPath}");
//     }
//     catch (Exception ex)
//     {
//         Console.WriteLine();
//         Console.WriteLine("Experiment failed and will be skipped:");
//         Console.WriteLine(ex.Message);
//     }
// }

// Console.WriteLine();
// Console.WriteLine("Done.");

// static string ResolveCsvPath(string[] args)
// {
//     const string csvPath = @"D:\Doktorat\bridge-optimization-lab\dotnet\Results.csv";

//     Console.WriteLine($"Using CSV file:");
//     Console.WriteLine(csvPath);
//     Console.WriteLine();

//     if (!File.Exists(csvPath))
//         throw new FileNotFoundException($"CSV file not found: {csvPath}");

//     return csvPath;
// }

// static string ResolveOutputDirectory(string folderName)
// {
//     // Put output next to the directory from which the app is launched.
//     // This is easy to find after clicking Run in Visual Studio/Rider.
//     return Path.GetFullPath(Path.Combine(Environment.CurrentDirectory, folderName));
// }

// static void PrintLabelStats(IReadOnlyList<BridgeMLApp.Domain.BeamRecord> rows)
// {
//     if (rows.Count == 0)
//     {
//         Console.WriteLine("No rows loaded.");
//         return;
//     }

//     var minLabel = rows.Min(r => r.Label);
//     var maxLabel = rows.Max(r => r.Label);
//     var avgLabel = rows.Average(r => r.Label);

//     Console.WriteLine("=== LABEL STATS ===");
//     Console.WriteLine($"Rows:  {rows.Count}");
//     Console.WriteLine($"Min:   {minLabel:F6}");
//     Console.WriteLine($"Max:   {maxLabel:F6}");
//     Console.WriteLine($"Avg:   {avgLabel:F6}");
//     Console.WriteLine($"Range: {(maxLabel - minLabel):F6}");
//     Console.WriteLine();
// }

// static void PrintRandomSamples(
//     IReadOnlyList<BridgeMLApp.Domain.BeamRecord> rows,
//     IReadOnlyList<string> featureNames,
//     int count)
// {
//     if (rows.Count == 0)
//         return;

//     var rng = new Random(1);

//     Console.WriteLine("=== RANDOM SAMPLES ===");

//     foreach (var row in rows.OrderBy(_ => rng.Next()).Take(count))
//     {
//         var preferredFeatureNames = new[]
//         {
//             "n_spans",
//             "total_span_length_m",
//             "beam_height_m",
//             "beam_width_m",
//             "n_tendons",
//             "tendon_force_kn",
//             "span_1_length_m",
//             "span_1_exists_mask",
//             "span_1_udl_kn_per_m",
//             "tendon_ecc_cp_0"
//         };

//         var featureStrings = preferredFeatureNames
//             .Select(name => new
//             {
//                 Name = name,
//                 Index = FindFeatureIndex(featureNames, name)
//             })
//             .Where(x => x.Index >= 0 && x.Index < row.Features.Length)
//             .Select(x => $"{x.Name}={row.Features[x.Index]:F4}");

//         Console.WriteLine(
//             $"Features: {string.Join(", ", featureStrings)} | " +
//             $"Label={row.Label:F6}");
//     }

//     Console.WriteLine();
// }

// static int FindFeatureIndex(IReadOnlyList<string> featureNames, string name)
// {
//     for (int i = 0; i < featureNames.Count; i++)
//     {
//         if (string.Equals(featureNames[i], name, StringComparison.OrdinalIgnoreCase))
//             return i;
//     }

//     return -1;
// }

// static void PrintRanking(
//     IReadOnlyList<RegressionResult> results,
//     int numberOfFolds)
// {

//     Console.WriteLine($"=== SUMMARY RESULTS ({numberOfFolds}-FOLD CROSS-VALIDATION) ===");

//     if (results.Count == 0)
//     {
//         Console.WriteLine("No model produced a valid result.");
//         return;
//     }

//     for (int i = 0; i < results.Count; i++)
//     {
//         var r = results[i];

//         Console.WriteLine(
//             $"{i + 1}. {r.ModelName,-22} | " +
//             $"R² = {r.AvgRSquared:F4} ± {r.StdRSquared:F4} | " +
//             $"MAE = {r.AvgMeanAbsoluteError:F6} ± {r.StdMeanAbsoluteError:F6} | " +
//             $"RMSE = {r.AvgRootMeanSquaredError:F6} ± {r.StdRootMeanSquaredError:F6}");
//     }
// }
using BridgeMLApp.Data;
using BridgeMLApp.Experiments;
using BridgeMLApp.ML;
using Microsoft.ML;

// ============================================================
// MULTI-SPAN ML TRAINING ENTRY POINT
// ============================================================

var csvPath = ResolveCsvPath(args);
var runName = DateTime.Now.ToString("yyyyMMdd_HHmmss");

var modelOutputDirectory = Path.Combine(
    @"D:\Doktorat\bridge-optimization-lab\dotnet\models_multi_span",
    $"run_{runName}");

var saveBestModel = true;

var selectedExperiments = MultiSpanExperimentCatalog.AllTotalExperiments().ToList();

var selectedModels = new[]
{
    RegressionModelType.LightGbm,
    RegressionModelType.FastTree,
};

var mlContext = new MLContext(seed: 1);

var featureBuilder = new MultiSpanFeatureBuilder();
var loader = new MultiSpanCsvBeamDataLoader(mlContext);
var comparer = new ModelComparer(mlContext);
var trainingService = new ModelTrainingService(mlContext);

Directory.CreateDirectory(modelOutputDirectory);

Console.WriteLine("MULTI-SPAN BEAM ML TRAINING");
Console.WriteLine($"CSV:         {csvPath}");
Console.WriteLine($"Output:      {modelOutputDirectory}");
Console.WriteLine($"Features:    {featureBuilder.FeatureCount}");
Console.WriteLine($"Experiments: {selectedExperiments.Count}");
Console.WriteLine();

for (int experimentIndex = 0; experimentIndex < selectedExperiments.Count; experimentIndex++)
{
    var experiment = selectedExperiments[experimentIndex];

    experiment.FeatureColumns = featureBuilder.FeatureNames.ToArray();

    Console.WriteLine($"[{experimentIndex + 1}/{selectedExperiments.Count}] {experiment.Name}");

    try
    {
        var data = RunWithMutedConsoleOutput(() => loader.Load(
            filePath: csvPath,
            targetColumn: experiment.TargetColumn,
            featureBuilder: featureBuilder));

        var rows = loader.LastLoadedRecords;

        if (rows.Count < 2)
        {
            Console.WriteLine($"  skipped: too few rows ({rows.Count})");
            continue;
        }

        var numberOfFolds = Math.Min(5, rows.Count);

        var results = comparer.CompareWithCrossValidation(
            data: data,
            numberOfFolds: numberOfFolds,
            selectedModels: selectedModels);

        if (results.Count == 0)
        {
            Console.WriteLine("  failed: no valid model result");
            continue;
        }

        var best = results.First();

        PrintExperimentSummary(
            rows: rows,
            skippedTargetMissing: loader.LastSkippedBecauseTargetMissing,
            skippedFeatureError: loader.LastSkippedBecauseFeatureError,
            numberOfFolds: numberOfFolds,
            results: results);

        if (!saveBestModel)
            continue;

        if (!Enum.TryParse<RegressionModelType>(best.ModelName, out var bestModelType))
        {
            Console.WriteLine($"  model not saved: could not parse model type '{best.ModelName}'");
            continue;
        }

        var savedModelPath = trainingService.TrainAndSave(
            data: data,
            experiment: experiment,
            modelType: bestModelType,
            outputDirectory: modelOutputDirectory);

        Console.WriteLine($"  saved: {Path.GetFileName(savedModelPath)}");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"  failed: {ex.Message}");
    }

    Console.WriteLine();
}

Console.WriteLine("Done.");

static string ResolveCsvPath(string[] args)
{
    const string defaultCsvPath = @"D:\Doktorat\bridge-optimization-lab\dotnet\Results.csv";

    var csvPath = args.Length > 0 && !string.IsNullOrWhiteSpace(args[0])
        ? args[0]
        : defaultCsvPath;

    csvPath = Path.GetFullPath(csvPath);

    if (!File.Exists(csvPath))
        throw new FileNotFoundException($"CSV file not found: {csvPath}");

    return csvPath;
}

static string ResolveOutputDirectory(string folderName)
{
    return Path.GetFullPath(Path.Combine(Environment.CurrentDirectory, folderName));
}

static void PrintExperimentSummary(
    IReadOnlyList<BridgeMLApp.Domain.BeamRecord> rows,
    int skippedTargetMissing,
    int skippedFeatureError,
    int numberOfFolds,
    IReadOnlyList<RegressionResult> results)
{
    var minLabel = rows.Min(r => r.Label);
    var maxLabel = rows.Max(r => r.Label);
    var avgLabel = rows.Average(r => r.Label);

    Console.WriteLine(
        $"  rows={rows.Count}, skipped_target={skippedTargetMissing}, skipped_features={skippedFeatureError}, " +
        $"label[min={minLabel:F4}, max={maxLabel:F4}, avg={avgLabel:F4}]");

    var modelSummary = results.Select(r =>
        $"{r.ModelName}: R2={r.AvgRSquared:F4}, MAE={r.AvgMeanAbsoluteError:F4}, RMSE={r.AvgRootMeanSquaredError:F4}");

    Console.WriteLine($"  models ({numberOfFolds}-fold): {string.Join(" | ", modelSummary)}");
    Console.WriteLine($"  best: {results.First().ModelName}");
}

static T RunWithMutedConsoleOutput<T>(Func<T> action)
{
    var originalOut = Console.Out;

    try
    {
        Console.SetOut(TextWriter.Null);
        return action();
    }
    finally
    {
        Console.SetOut(originalOut);
    }
}