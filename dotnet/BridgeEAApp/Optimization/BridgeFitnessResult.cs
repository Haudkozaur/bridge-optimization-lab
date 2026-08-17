namespace BridgeEAApp.Optimization;

public class BridgeFitnessResult
{
    public float Fitness { get; set; }

    public float StructuralScore { get; set; }
    public float DeflectionScore { get; set; }
    public float SpanMomentScore { get; set; }
    public float SupportMomentScore { get; set; }
    public float ReactionScore { get; set; }
    public float SymmetryScore { get; set; }
    public bool SymmetryPenaltyApplied { get; set; }
    public float CoverPenaltyScore { get; set; }
    public float SmoothnessPenaltyScore { get; set; }
    public float JumpPenaltyScore { get; set; }

    public Dictionary<string, float> Predictions { get; } = new();

    public float[] SpanDeflectionAbsMax { get; set; } = [];
    public float[] SpanMomentMin { get; set; } = [];
    public float[] SpanMomentMax { get; set; } = [];
    public float[] SpanMomentAbsMax { get; set; } = [];

    public float[] SupportDeflectionAbsMax { get; set; } = [];
    public float[] SupportMomentMin { get; set; } = [];
    public float[] SupportMomentMax { get; set; } = [];
    public float[] SupportMomentAbsMax { get; set; } = [];
    public float[] SupportReactionFz { get; set; } = [];
}