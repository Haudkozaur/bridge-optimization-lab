using BridgeMLApp.Data;
using BridgeMLApp.Domain;
using BridgeMLApp.Experiments;
using BridgeMLApp.ML;
using BridgeMLApp.Reporting;
using Microsoft.ML;

string filePath = Path.GetFullPath(
    Path.Combine(
        AppDomain.CurrentDomain.BaseDirectory,
        @"..\..\..\..\results_ml_ready.csv"));

var saveBestModel = true;

var selectedExperiments = new[]
{
    ExperimentCatalog.MiddleHyperstaticReaction,

    //ExperimentCatalog.TotalMomentLeftSpanAbsMax,
    ExperimentCatalog.TotalMomentMiddleSupport,
    //ExperimentCatalog.TotalMomentRightSpanAbsMax,

    ExperimentCatalog.TotalDeflectionLeftSpanAbsMax,
    ExperimentCatalog.TotalDeflectionRightSpanAbsMax,

     ExperimentCatalog.TotalMomentLeftSpanMin,
     ExperimentCatalog.TotalMomentLeftSpanMax,
     ExperimentCatalog.TotalMomentRightSpanMin,
     ExperimentCatalog.TotalMomentRightSpanMax,
    //  ExperimentCatalog.TotalMomentLeftSupportFromLeftEcc,
    //  ExperimentCatalog.TotalMomentRightSupportFromRightEcc,
     ExperimentCatalog.TotalDeflectionLeftSpanMin,
     ExperimentCatalog.TotalDeflectionLeftSpanMax,
     ExperimentCatalog.TotalDeflectionRightSpanMin,
     ExperimentCatalog.TotalDeflectionRightSpanMax,
};

var selectedModels = new[]
{
    RegressionModelType.LightGbm
    // RegressionModelType.FastTree
};

var mlContext = new MLContext(seed: 1);

var loader = new CsvBeamDataLoader(mlContext);
var comparer = new ModelComparer(mlContext);
var trainingService = new ModelTrainingService(mlContext);

var modelOutputDirectory = Path.GetFullPath(
    Path.Combine(
        AppDomain.CurrentDomain.BaseDirectory,
        @"..\..\..\..\models"));

foreach (var experiment in selectedExperiments)
{
    Console.WriteLine();
    Console.WriteLine("==================================================");
    Console.WriteLine($"EXPERIMENT: {experiment.Name}");
    Console.WriteLine("==================================================");

    IDataView data = loader.Load(
        filePath,
        experiment.TargetColumn,
        experiment.FeatureColumns);

    var rows = mlContext.Data
        .CreateEnumerable<BeamRecord>(data, reuseRowObject: false)
        .ToList();

    ConsoleReportPrinter.PrintExperimentInfo(experiment);
    ConsoleReportPrinter.PrintLabelStats(rows);
    ConsoleReportPrinter.PrintRandomSamples(rows, experiment);

    var results = comparer.CompareWithCrossValidation(
        data,
        numberOfFolds: 5,
        selectedModels);

    ConsoleReportPrinter.PrintRanking(results);

    if (!saveBestModel || results.Count == 0)
        continue;

    var bestResult = results.First();
    var modelToSave = Enum.Parse<RegressionModelType>(bestResult.ModelName);

    var savedModelPath = trainingService.TrainAndSave(
        data,
        experiment,
        modelToSave,
        modelOutputDirectory);

    Console.WriteLine();
    Console.WriteLine($"Saved best model: {savedModelPath}");
}