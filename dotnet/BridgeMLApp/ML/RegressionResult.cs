namespace BridgeMLApp.ML;

public class RegressionResult
{
    public string ModelName { get; set; } = string.Empty;

    public double AvgRSquared { get; set; }
    public double AvgMeanAbsoluteError { get; set; }
    public double AvgRootMeanSquaredError { get; set; }

    public double StdRSquared { get; set; }
    public double StdMeanAbsoluteError { get; set; }
    public double StdRootMeanSquaredError { get; set; }
}