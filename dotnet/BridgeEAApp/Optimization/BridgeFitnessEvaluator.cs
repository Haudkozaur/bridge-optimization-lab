using BridgeEAApp.Surrogate;

namespace BridgeEAApp.Optimization;

public class BridgeFitnessEvaluator
{
    private readonly IReadOnlyDictionary<string, MlSurrogateModel> _models;

    private const float DeflectionReference = 0.05f;          // m
    private const float SpanMomentReference = 1500.0f;        // kNm
    private const float SupportMomentReference = 2500.0f;     // kNm
    private const float EccReference = 0.05f;                 // m

    private const float DeflectionWeight = 1.0f;
    private const float SpanMomentWeight = 1.0f;
    private const float SupportMomentWeight = 1.0f;

    // Startowo umiarkowanie. Jak dalej będzie krzywo, daj 0.35–0.50.
    private const float SymmetryPenaltyWeight = 0.25f;

    private const float SpanLengthSymmetryToleranceM = 0.01f;
    private const float UdlSymmetryToleranceKnPerM = 0.001f;

    public BridgeFitnessEvaluator(
        IReadOnlyDictionary<string, MlSurrogateModel> models)
    {
        _models = models;
    }

    public BridgeFitnessResult EvaluateDetailed(BridgeCandidate candidate)
    {
        candidate.Validate();

        var features = MultiSpanFeatureBuilder.Build(candidate);

        var result = new BridgeFitnessResult
        {
            SpanDeflectionAbsMax = new float[candidate.NSpans],
            SpanMomentMin = new float[candidate.NSpans],
            SpanMomentMax = new float[candidate.NSpans],
            SpanMomentAbsMax = new float[candidate.NSpans],

            SupportDeflectionAbsMax = new float[candidate.NSpans + 1],
            SupportMomentMin = new float[candidate.NSpans + 1],
            SupportMomentMax = new float[candidate.NSpans + 1],
            SupportMomentAbsMax = new float[candidate.NSpans + 1],

            SupportReactionFz = new float[candidate.NSpans + 1]
        };

        // =========================
        // SPANS
        // =========================
        for (var span = 1; span <= candidate.NSpans; span++)
        {
            var spanIndex = span - 1;

            result.SpanDeflectionAbsMax[spanIndex] =
                PredictRequired(
                    $"total_deflection_span_{span}_middle_zone_abs_max",
                    features,
                    result);

            result.SpanMomentMin[spanIndex] =
                PredictRequired(
                    $"total_moment_span_{span}_middle_zone_min",
                    features,
                    result);

            result.SpanMomentMax[spanIndex] =
                PredictRequired(
                    $"total_moment_span_{span}_middle_zone_max",
                    features,
                    result);

            result.SpanMomentAbsMax[spanIndex] =
                PredictRequired(
                    $"total_moment_span_{span}_middle_zone_abs_max",
                    features,
                    result);

            result.DeflectionScore +=
                Math.Abs(result.SpanDeflectionAbsMax[spanIndex]) / DeflectionReference;

            var spanMomentEnvelope = MaxAbs(
                result.SpanMomentMin[spanIndex],
                result.SpanMomentMax[spanIndex],
                result.SpanMomentAbsMax[spanIndex]);

            result.SpanMomentScore +=
                spanMomentEnvelope / SpanMomentReference;
        }

        // =========================
        // SUPPORTS
        // =========================
        for (var support = 0; support <= candidate.NSpans; support++)
        {
            result.SupportDeflectionAbsMax[support] =
                PredictRequired(
                    $"total_deflection_support_{support}_zone_abs_max",
                    features,
                    result);

            result.SupportMomentMin[support] =
                PredictRequired(
                    $"total_moment_support_{support}_zone_min",
                    features,
                    result);

            result.SupportMomentMax[support] =
                PredictRequired(
                    $"total_moment_support_{support}_zone_max",
                    features,
                    result);

            result.SupportMomentAbsMax[support] =
                PredictRequired(
                    $"total_moment_support_{support}_zone_abs_max",
                    features,
                    result);

            result.DeflectionScore +=
                Math.Abs(result.SupportDeflectionAbsMax[support]) / DeflectionReference;

            var supportMomentEnvelope = MaxAbs(
                result.SupportMomentMin[support],
                result.SupportMomentMax[support],
                result.SupportMomentAbsMax[support]);

            result.SupportMomentScore +=
                supportMomentEnvelope / SupportMomentReference;
        }

        result.ReactionScore = 0.0f;
        result.CoverPenaltyScore = 0.0f;
        result.SmoothnessPenaltyScore = 0.0f;
        result.JumpPenaltyScore = 0.0f;

        result.SymmetryPenaltyApplied =
            ShouldApplySymmetryPenalty(candidate);

        result.SymmetryScore =
            result.SymmetryPenaltyApplied
                ? CalculateSymmetryPenalty(candidate)
                : 0.0f;

        result.StructuralScore =
            DeflectionWeight * result.DeflectionScore +
            SpanMomentWeight * result.SpanMomentScore +
            SupportMomentWeight * result.SupportMomentScore;

        result.Fitness =
            result.StructuralScore +
            SymmetryPenaltyWeight * result.SymmetryScore;

        return result;
    }

    private float PredictRequired(
        string targetName,
        float[] features,
        BridgeFitnessResult result)
    {
        if (!_models.TryGetValue(targetName, out var model))
        {
            throw new Exception(
                $"Required ML model not found: {targetName}. " +
                $"Available models: {_models.Count}");
        }

        var value = model.Predict(features);
        result.Predictions[targetName] = value;

        return value;
    }

    private static bool ShouldApplySymmetryPenalty(BridgeCandidate candidate)
    {
        for (var i = 0; i < candidate.NSpans / 2; i++)
        {
            var j = candidate.NSpans - 1 - i;

            var leftLength = candidate.SpanLengthsM[i];
            var rightLength = candidate.SpanLengthsM[j];

            if (Math.Abs(leftLength - rightLength) > SpanLengthSymmetryToleranceM)
                return false;

            var leftUdl = candidate.UdlValuesKnPerM[i];
            var rightUdl = candidate.UdlValuesKnPerM[j];

            if (Math.Abs(leftUdl - rightUdl) > UdlSymmetryToleranceKnPerM)
                return false;
        }

        return true;
    }

    private static float CalculateSymmetryPenalty(BridgeCandidate candidate)
    {
        var activeCpCount = candidate.ActiveTendonControlPointCount;
        var pairCount = activeCpCount / 2;

        if (pairCount == 0)
            return 0.0f;

        var penalty = 0.0f;

        for (var i = 0; i < pairCount; i++)
        {
            var j = activeCpCount - 1 - i;

            var left = candidate.TendonEccControlPointsM[i];
            var right = candidate.TendonEccControlPointsM[j];

            var normalizedDiff =
                Math.Abs(left - right) / EccReference;

            penalty += normalizedDiff;
        }

        // Uśredniamy, żeby kara nie rosła automatycznie tylko dlatego,
        // że belka ma więcej przęseł i więcej punktów kabla.
        return penalty / pairCount;
    }

    private static float MaxAbs(params float[] values)
    {
        var max = 0.0f;

        foreach (var value in values)
        {
            var abs = Math.Abs(value);

            if (abs > max)
                max = abs;
        }

        return max;
    }
}