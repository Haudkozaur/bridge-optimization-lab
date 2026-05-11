using BridgeMLApp.Domain;
using Microsoft.ML;

namespace BridgeMLApp.ML;

public class ModelTrainingService
{
    private readonly MLContext _mlContext;

    public ModelTrainingService(MLContext mlContext)
    {
        _mlContext = mlContext;
    }

    public string TrainAndSave(
        IDataView data,
        MlExperiment experiment,
        RegressionModelType modelType,
        string outputDirectory)
    {
        var pipeline = BuildPipeline(modelType);

        var model = pipeline.Fit(data);

        Directory.CreateDirectory(outputDirectory);

        var modelPath = Path.Combine(
            outputDirectory,
            $"{experiment.Name}_{modelType}.zip");

        _mlContext.Model.Save(model, data.Schema, modelPath);

        return modelPath;
    }

    private IEstimator<ITransformer> BuildPipeline(RegressionModelType modelType)
    {
        return modelType switch
        {
            RegressionModelType.FastTree => BuildFastTreePipeline(),
            RegressionModelType.LightGbm => BuildLightGbmPipeline(),
            RegressionModelType.GAM => BuildGamPipeline(),
            RegressionModelType.SDCA => BuildSdcaPipeline(),
            RegressionModelType.FastForest => BuildFastForestPipeline(),
            RegressionModelType.OnlineGradientDescent => BuildOnlineGradientDescentPipeline(),
            _ => throw new ArgumentOutOfRangeException(nameof(modelType), modelType, null)
        };
    }

    private IEstimator<ITransformer> BuildBaseFeatures()
    {
        return _mlContext.Transforms.CopyColumns(
            outputColumnName: "Features",
            inputColumnName: nameof(BeamRecord.Features));
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

    private IEstimator<ITransformer> BuildSdcaPipeline()
    {
        return BuildBaseFeatures()
            .Append(_mlContext.Transforms.NormalizeMeanVariance("Features"))
            .Append(_mlContext.Regression.Trainers.Sdca(
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

    private IEstimator<ITransformer> BuildOnlineGradientDescentPipeline()
    {
        return BuildBaseFeatures()
            .Append(_mlContext.Transforms.NormalizeMeanVariance("Features"))
            .Append(_mlContext.Regression.Trainers.OnlineGradientDescent(
                labelColumnName: "Label",
                featureColumnName: "Features"));
    }
}