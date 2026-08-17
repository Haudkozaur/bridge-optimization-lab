using BridgeMLApp.Domain;
using Microsoft.ML;
using Microsoft.ML.Data;

namespace BridgeEAApp.Surrogate;

public class MlSurrogateModel
{
    private readonly PredictionEngine<BeamRecord, BeamPrediction> _predictionEngine;

    public string Name { get; }

    public MlSurrogateModel(string name, string modelPath)
    {
        Name = name;

        var mlContext = new MLContext(seed: 1);

        var model = mlContext.Model.Load(modelPath, out _);

        var inputSchemaDefinition = SchemaDefinition.Create(typeof(BeamRecord));
        inputSchemaDefinition[nameof(BeamRecord.Features)].ColumnType =
            new VectorDataViewType(
                NumberDataViewType.Single,
                MultiSpanFeatureBuilder.FeatureCount);

        _predictionEngine =
            mlContext.Model.CreatePredictionEngine<BeamRecord, BeamPrediction>(
                model,
                inputSchemaDefinition: inputSchemaDefinition);
    }

    public float Predict(float[] features)
    {
        if (features.Length != MultiSpanFeatureBuilder.FeatureCount)
        {
            throw new Exception(
                $"Feature vector size mismatch. Expected {MultiSpanFeatureBuilder.FeatureCount}, got {features.Length}.");
        }

        var input = new BeamRecord
        {
            Features = features
        };

        return _predictionEngine.Predict(input).Score;
    }
}