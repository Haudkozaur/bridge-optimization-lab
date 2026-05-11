using BridgeMLApp.Domain;
using Microsoft.ML;
using Microsoft.ML.Data;

namespace BridgeEAApp.Surrogate;

public class MlSurrogateModel
{
    private readonly PredictionEngine<BeamRecord, BeamPrediction> _predictionEngine;
    private readonly bool _includeUdl;

    public MlSurrogateModel(string modelPath, bool includeUdl)
    {
        _includeUdl = includeUdl;

        var mlContext = new MLContext();

        var model = mlContext.Model.Load(modelPath, out _);

        var featureCount = includeUdl ? 8 : 7;

        var inputSchemaDefinition = SchemaDefinition.Create(typeof(BeamRecord));
        inputSchemaDefinition[nameof(BeamRecord.Features)].ColumnType =
            new VectorDataViewType(NumberDataViewType.Single, featureCount);

        _predictionEngine =
            mlContext.Model.CreatePredictionEngine<BeamRecord, BeamPrediction>(
                model,
                inputSchemaDefinition: inputSchemaDefinition);
    }

    public float Predict(BridgeCandidate candidate)
    {
        var input = new BeamRecord
        {
            Features = candidate.ToFeatures(_includeUdl)
        };

        return _predictionEngine.Predict(input).Score;
    }
}