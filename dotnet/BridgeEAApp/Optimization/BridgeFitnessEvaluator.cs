using BridgeEAApp.Surrogate;

namespace BridgeEAApp.Optimization;

public class BridgeFitnessEvaluator
{
    private readonly MlSurrogateModel _middlePsReactionModel;
    private readonly MlSurrogateModel _middleTotalMomentModel;

    private readonly MlSurrogateModel _leftDeflectionMinModel;
    private readonly MlSurrogateModel _leftDeflectionMaxModel;
    private readonly MlSurrogateModel _rightDeflectionMinModel;
    private readonly MlSurrogateModel _rightDeflectionMaxModel;

    private readonly MlSurrogateModel _leftMomentMinModel;
    private readonly MlSurrogateModel _leftMomentMaxModel;
    private readonly MlSurrogateModel _rightMomentMinModel;
    private readonly MlSurrogateModel _rightMomentMaxModel;

    private const float PrestressForceKn = 660.0f;


    // reference values used to normalize units

    private const float EndSupportMomentReference = 300.0f;        // kNm, A/C moments
    private const float MiddlePsReactionReference = 100.0f;        // kN, B hyperstatic reaction
    private const float MiddleSupportMomentReference = 1500.0f;    // kNm, B total moment

    private const float SpanMomentReference = 1000.0f;             // kNm
    private const float DeflectionReference = 0.05f;               // m
    private const float EccReference = 0.05f;                      // m

    // importance weights
    private const float HyperstaticEffectWeight = 1.0f;
    private const float MiddleSupportMomentWeight = 1.0f;
    private const float SpanMomentWeight = 1.0f;
    private const float DeflectionWeight = 1.0f;
    private const float SymmetryWeight = 0.25f;

    // to chec if symmetry penalty should be applied
    private const float SpanLengthTolerance = 0.01f;


    public BridgeFitnessEvaluator(
        MlSurrogateModel middlePsReactionModel,
        MlSurrogateModel middleTotalMomentModel,
        MlSurrogateModel leftDeflectionMinModel,
        MlSurrogateModel leftDeflectionMaxModel,
        MlSurrogateModel rightDeflectionMinModel,
        MlSurrogateModel rightDeflectionMaxModel,
        MlSurrogateModel leftMomentMinModel,
        MlSurrogateModel leftMomentMaxModel,
        MlSurrogateModel rightMomentMinModel,
        MlSurrogateModel rightMomentMaxModel)
    {
        _middlePsReactionModel = middlePsReactionModel;
        _middleTotalMomentModel = middleTotalMomentModel;

        _leftDeflectionMinModel = leftDeflectionMinModel;
        _leftDeflectionMaxModel = leftDeflectionMaxModel;
        _rightDeflectionMinModel = rightDeflectionMinModel;
        _rightDeflectionMaxModel = rightDeflectionMaxModel;

        _leftMomentMinModel = leftMomentMinModel;
        _leftMomentMaxModel = leftMomentMaxModel;
        _rightMomentMinModel = rightMomentMinModel;
        _rightMomentMaxModel = rightMomentMaxModel;
    }

    public BridgeFitnessResult EvaluateDetailed(BridgeCandidate candidate)
    {
        // A and C are deterministic from eccentricity
        var momentA = candidate.TendonEccLeftM * PrestressForceKn;
        var momentC = candidate.TendonEccRightM * PrestressForceKn;

        // B support
        var momentBPs = _middlePsReactionModel.Predict(candidate);
        var momentBTotal = _middleTotalMomentModel.Predict(candidate);

        // Deflections
        var leftDeflectionMin = _leftDeflectionMinModel.Predict(candidate);
        var leftDeflectionMax = _leftDeflectionMaxModel.Predict(candidate);
        var rightDeflectionMin = _rightDeflectionMinModel.Predict(candidate);
        var rightDeflectionMax = _rightDeflectionMaxModel.Predict(candidate);

        // Span moments
        var leftMomentMin = _leftMomentMinModel.Predict(candidate);
        var leftMomentMax = _leftMomentMaxModel.Predict(candidate);
        var rightMomentMin = _rightMomentMinModel.Predict(candidate);
        var rightMomentMax = _rightMomentMaxModel.Predict(candidate);

        var endSupportMomentScore =
            Math.Abs(momentA) / EndSupportMomentReference +
            Math.Abs(momentC) / EndSupportMomentReference;

        var middlePsReactionScore =
            Math.Abs(momentBPs) / MiddlePsReactionReference;

        var hyperstaticEffectScore =
            endSupportMomentScore +
            middlePsReactionScore;

        var middleSupportMomentScore =
            Math.Abs(momentBTotal) / MiddleSupportMomentReference;

        var deflectionScore =
            Math.Abs(leftDeflectionMin) / DeflectionReference +
            Math.Abs(leftDeflectionMax) / DeflectionReference +
            Math.Abs(rightDeflectionMin) / DeflectionReference +
            Math.Abs(rightDeflectionMax) / DeflectionReference;

        var spanMomentScore =
            Math.Abs(leftMomentMin) / SpanMomentReference +
            Math.Abs(leftMomentMax) / SpanMomentReference +
            Math.Abs(rightMomentMin) / SpanMomentReference +
            Math.Abs(rightMomentMax) / SpanMomentReference;

        var symmetryPenaltyApplied =
            Math.Abs(candidate.LeftSpanLengthM - candidate.RightSpanLengthM) < SpanLengthTolerance;

        var symmetryScore = 0.0f;

        if (symmetryPenaltyApplied)
        {
            symmetryScore =
        Math.Abs(candidate.TendonEccLeftM - candidate.TendonEccRightM) / EccReference +
        Math.Abs(candidate.TendonEccLeftSpanMidM - candidate.TendonEccRightSpanMidM) / EccReference;
        }

        var fitness =
            HyperstaticEffectWeight * hyperstaticEffectScore +
            MiddleSupportMomentWeight * middleSupportMomentScore +
            DeflectionWeight * deflectionScore +
            SpanMomentWeight * spanMomentScore +
            SymmetryWeight * symmetryScore;

        return new BridgeFitnessResult
        {
            Fitness = fitness,

            MomentA = momentA,
            MomentBPs = momentBPs,
            MomentBTotal = momentBTotal,
            MomentC = momentC,

            LeftDeflectionMin = leftDeflectionMin,
            LeftDeflectionMax = leftDeflectionMax,
            RightDeflectionMin = rightDeflectionMin,
            RightDeflectionMax = rightDeflectionMax,

            LeftMomentMin = leftMomentMin,
            LeftMomentMax = leftMomentMax,
            RightMomentMin = rightMomentMin,
            RightMomentMax = rightMomentMax,

            HyperstaticEffectScore = hyperstaticEffectScore,
            MiddleSupportMomentScore = middleSupportMomentScore,
            DeflectionScore = deflectionScore,
            SpanMomentScore = spanMomentScore,

            SymmetryScore = symmetryScore,
            SymmetryPenaltyApplied = symmetryPenaltyApplied
        };
    }
}