using BridgeMLApp.Domain;
using Microsoft.ML;

namespace BridgeMLApp.ML;

public class ModelComparer
{
    private readonly MLContext _mlContext;

    public ModelComparer(MLContext mlContext)
    {
        _mlContext = mlContext;
    }

    public List<RegressionResult> CompareWithCrossValidation(
        IDataView data,
        int numberOfFolds,
        IReadOnlyCollection<RegressionModelType>? selectedModels = null)
    {
        selectedModels ??= Enum.GetValues<RegressionModelType>();

        var results = new List<RegressionResult>();

        var models = new List<(RegressionModelType Type, string Name, IEstimator<ITransformer> Pipeline)>
        {
            (RegressionModelType.FastTree, "FastTree", BuildFastTreePipeline()),
            (RegressionModelType.LightGbm, "LightGbm", BuildLightGbmPipeline()),
            (RegressionModelType.GAM, "GAM", BuildGamPipeline()),
            (RegressionModelType.SDCA, "SDCA", BuildSdcaPipeline()),
            (RegressionModelType.FastForest, "FastForest", BuildFastForestPipeline()),
            (RegressionModelType.OnlineGradientDescent, "OnlineGradientDescent", BuildOnlineGradientDescentPipeline())
        };

        foreach (var (type, name, pipeline) in models.Where(m => selectedModels.Contains(m.Type)))
        {
            try
            {
                var cvResults = _mlContext.Regression.CrossValidate(
                    data: data,
                    estimator: pipeline,
                    numberOfFolds: numberOfFolds,
                    labelColumnName: "Label");

                var r2 = cvResults.Select(x => x.Metrics.RSquared).ToList();
                var mae = cvResults.Select(x => x.Metrics.MeanAbsoluteError).ToList();
                var rmse = cvResults.Select(x => x.Metrics.RootMeanSquaredError).ToList();

                var result = new RegressionResult
                {
                    ModelName = name,
                    AvgRSquared = r2.Average(),
                    AvgMeanAbsoluteError = mae.Average(),
                    AvgRootMeanSquaredError = rmse.Average(),

                    StdRSquared = StdDev(r2),
                    StdMeanAbsoluteError = StdDev(mae),
                    StdRootMeanSquaredError = StdDev(rmse)
                };

                results.Add(result);
            }
            catch (Exception ex)
            {
                Console.WriteLine();
                Console.WriteLine($"=== {name} ===");
                Console.WriteLine("Model failed:");
                Console.WriteLine(ex.Message);
            }
        }

        return results
            .OrderByDescending(r => r.AvgRSquared)
            .ThenBy(r => r.AvgRootMeanSquaredError)
            .ToList();
    }

    private static double StdDev(List<double> values)
    {
        if (values.Count <= 1)
            return 0.0;

        var avg = values.Average();
        var variance = values.Sum(v => Math.Pow(v - avg, 2)) / values.Count;
        return Math.Sqrt(variance);
    }

    private IEstimator<ITransformer> BuildBaseFeatures()
    {
        return _mlContext.Transforms.CopyColumns(
            outputColumnName: "Features",
            inputColumnName: nameof(BeamRecord.Features));
    }

    private IEstimator<ITransformer> BuildSdcaPipeline()
    {
        return BuildBaseFeatures()
            .Append(_mlContext.Transforms.NormalizeMeanVariance("Features"))
            .Append(_mlContext.Regression.Trainers.Sdca(
                labelColumnName: "Label",
                featureColumnName: "Features"));
    }

    private IEstimator<ITransformer> BuildOnlineGradientDescentPipeline()
    {
        return BuildBaseFeatures()
            .Append(_mlContext.Transforms.NormalizeMeanVariance("Features"))
            .Append(_mlContext.Regression.Trainers.OnlineGradientDescent(
                labelColumnName: "Label",
                featureColumnName: "Features"));
    }

    private IEstimator<ITransformer> BuildFastForestPipeline()
    {
        return BuildBaseFeatures()
            .Append(_mlContext.Regression.Trainers.FastForest(
                labelColumnName: "Label",
                featureColumnName: "Features",
                numberOfLeaves: 20,
                numberOfTrees: 200,
                minimumExampleCountPerLeaf: 2));
    }

    private IEstimator<ITransformer> BuildFastTreePipeline()
    {
        return BuildBaseFeatures()
            .Append(_mlContext.Regression.Trainers.FastTree(
                labelColumnName: "Label",
                featureColumnName: "Features",
                numberOfLeaves: 20,
                numberOfTrees: 200,
                minimumExampleCountPerLeaf: 2,
                learningRate: 0.1));
    }

    private IEstimator<ITransformer> BuildLightGbmPipeline()
    {
        return BuildBaseFeatures()
            .Append(_mlContext.Regression.Trainers.LightGbm(
                labelColumnName: "Label",
                featureColumnName: "Features",
                numberOfLeaves: 20,
                numberOfIterations: 200,
                minimumExampleCountPerLeaf: 2,
                learningRate: 0.1));
    }

    private IEstimator<ITransformer> BuildGamPipeline()
    {
        return BuildBaseFeatures()
            .Append(_mlContext.Regression.Trainers.Gam(
                labelColumnName: "Label",
                featureColumnName: "Features"));
    }
}