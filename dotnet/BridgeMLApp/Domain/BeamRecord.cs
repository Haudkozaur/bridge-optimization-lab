using Microsoft.ML.Data;

namespace BridgeMLApp.Domain;

public class BeamRecord
{
    [VectorType]
    public float[] Features { get; set; } = [];

    [ColumnName("Label")]
    public float Label { get; set; }
}