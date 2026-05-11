namespace BridgeEAApp.Optimization;

public class BridgeFitnessResult
{
    public float Fitness { get; set; }

    // Scores
    public float HyperstaticEffectScore { get; set; }
    public float MiddleSupportMomentScore { get; set; }
    public float DeflectionScore { get; set; }
    public float SpanMomentScore { get; set; }

    // Symmetry penalty
    public float SymmetryScore { get; set; }
    public bool SymmetryPenaltyApplied { get; set; }

    // Supports
    public float MomentA { get; set; }
    public float MomentBPs { get; set; }
    public float MomentBTotal { get; set; }
    public float MomentC { get; set; }

    // Deflections
    public float LeftDeflectionMin { get; set; }
    public float LeftDeflectionMax { get; set; }
    public float RightDeflectionMin { get; set; }
    public float RightDeflectionMax { get; set; }

    // Span moments
    public float LeftMomentMin { get; set; }
    public float LeftMomentMax { get; set; }
    public float RightMomentMin { get; set; }
    public float RightMomentMax { get; set; }
}