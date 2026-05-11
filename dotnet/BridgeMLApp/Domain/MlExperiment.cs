namespace BridgeMLApp.Domain;

public class MlExperiment
{
    public string Name { get; set; } = string.Empty;

    public string TargetColumn { get; set; } = string.Empty;

    public string[] FeatureColumns { get; set; } = [];
}