using BridgeEAApp.Surrogate;

namespace BridgeEAApp.Optimization;

public class RandomSearchOptimizer
{
    private readonly Random _random = new(1);

    private const float MutationProbability = 0.85f;
    private const float MutationMaxDelta = 0.025f;

    private const float RandomRestartProbability = 0.10f;
    private const float SnapToZeroTolerance = 0.0025f;

    public BridgeCandidate Optimize(
        BridgeCandidate template,
        int iterations,
        int patience,
        OptimizationMode mode,
        BridgeFitnessEvaluator fitnessEvaluator)
    {
        template.Validate();

        BridgeCandidate? bestCandidate = null;
        var bestFitness = float.MaxValue;
        var iterationsWithoutImprovement = 0;

        for (var i = 0; i < iterations; i++)
        {
            BridgeCandidate candidate;

            if (bestCandidate == null)
            {
                candidate = CreateZeroCandidate(template);
            }
            else if (mode == OptimizationMode.MonteCarlo)
            {
                candidate = CreateRandomCandidate(template);
            }
            else if (
                mode == OptimizationMode.MutationAroundBest &&
                _random.NextDouble() < MutationProbability)
            {
                candidate = Mutate(bestCandidate);
            }
            else if (
                mode == OptimizationMode.MutationWithRandomRestart &&
                _random.NextDouble() > RandomRestartProbability)
            {
                candidate = Mutate(bestCandidate);
            }
            else
            {
                candidate = CreateRandomCandidate(template);
            }

            var result = fitnessEvaluator.EvaluateDetailed(candidate);
            var fitness = result.Fitness;

            if (fitness < bestFitness)
            {
                bestFitness = fitness;
                bestCandidate = candidate;
                iterationsWithoutImprovement = 0;

                Console.WriteLine(
                    $"Iter {i,8} | " +
                    $"fitness = {fitness,12:F6} | " +
                    $"struct = {result.StructuralScore,10:F4} | " +
                    $"cover = {result.CoverPenaltyScore,8:F4} | " +
                    $"smooth = {result.SmoothnessPenaltyScore,8:F4} | " +
                    $"jump = {result.JumpPenaltyScore,8:F4} | " +
                    $"sym = {result.SymmetryScore,8:F4} | " +
                    $"ecc = {FormatEccPreview(candidate)}");
            }
            else
            {
                iterationsWithoutImprovement++;
            }

            if (iterationsWithoutImprovement >= patience)
            {
                Console.WriteLine();
                Console.WriteLine(
                    $"Stopped after {i} iterations - no improvement for {patience} iterations.");
                break;
            }
        }

        return bestCandidate
            ?? throw new Exception("Optimization failed.");
    }

    private BridgeCandidate CreateZeroCandidate(BridgeCandidate template)
    {
        var candidate = template.Clone();

        for (var i = 0; i < BridgeCandidate.MaxTendonControlPoints; i++)
            candidate.TendonEccControlPointsM[i] = 0.0f;

        return candidate;
    }

    private BridgeCandidate CreateRandomCandidate(BridgeCandidate template)
    {
        var candidate = template.Clone();

        for (var i = 0; i < candidate.ActiveTendonControlPointCount; i++)
            candidate.TendonEccControlPointsM[i] = RandomEcc(candidate);

        for (var i = candidate.ActiveTendonControlPointCount;
             i < BridgeCandidate.MaxTendonControlPoints;
             i++)
        {
            candidate.TendonEccControlPointsM[i] = 0.0f;
        }

        return candidate;
    }

    private BridgeCandidate Mutate(BridgeCandidate parent)
    {
        var candidate = parent.Clone();

        for (var i = 0; i < candidate.ActiveTendonControlPointCount; i++)
        {
            if (_random.NextDouble() < MutationProbability)
            {
                candidate.TendonEccControlPointsM[i] =
                    MutateEcc(candidate, candidate.TendonEccControlPointsM[i]);
            }
        }

        for (var i = candidate.ActiveTendonControlPointCount;
             i < BridgeCandidate.MaxTendonControlPoints;
             i++)
        {
            candidate.TendonEccControlPointsM[i] = 0.0f;
        }

        return candidate;
    }

    private float MutateEcc(BridgeCandidate candidate, float value)
    {
        var delta =
            ((float)_random.NextDouble() * 2.0f - 1.0f) * MutationMaxDelta;

        var limit = GetEccLimit(candidate);
        var mutated = Math.Clamp(value + delta, -limit, limit);

        if (Math.Abs(mutated) < SnapToZeroTolerance)
            return 0.0f;

        return mutated;
    }

    private float RandomEcc(BridgeCandidate candidate)
    {
        var limit = GetEccLimit(candidate);

        return -limit + (float)_random.NextDouble() * 2.0f * limit;
    }

    private static float GetEccLimit(BridgeCandidate candidate)
    {
        var limit =
            candidate.BeamHeightM / 2.0f -
            candidate.TendonCoverM -
            0.005f;

        return Math.Max(0.01f, limit);
    }

    private static string FormatEccPreview(BridgeCandidate candidate)
    {
        var active = candidate.ActiveTendonControlPointCount;

        var values = candidate.TendonEccControlPointsM
            .Take(active)
            .Select(x => x.ToString("F3"));

        return "[" + string.Join(", ", values) + "]";
    }
}