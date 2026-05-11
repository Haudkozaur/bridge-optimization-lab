using BridgeEAApp.Surrogate;

namespace BridgeEAApp.Optimization;

public class RandomSearchOptimizer
{
    private readonly Random _random = new(1);

    private const float EccMin = -0.45f;
    private const float EccMax = 0.45f;

    private const float MutationProbability = 0.85f;
    private const float MutationMaxDelta = 0.025f;

    private const float RandomRestartProbability = 0.10f;
    private const float SnapToZeroTolerance = 0.0025f;

    public BridgeCandidate Optimize(
        float leftSpanLengthM,
        float rightSpanLengthM,
        float udlKnPerM,
        int iterations,
        int patience,
        OptimizationMode mode,
        BridgeFitnessEvaluator fitnessEvaluator)
    {
        BridgeCandidate? bestCandidate = null;
        var bestFitness = float.MaxValue;
        var iterationsWithoutImprovement = 0;

        for (int i = 0; i < iterations; i++)
        {
            BridgeCandidate candidate;

            if (bestCandidate == null)
            {
                candidate = CreateZeroCandidate(
                    leftSpanLengthM,
                    rightSpanLengthM,
                    udlKnPerM);
            }
            else if (mode == OptimizationMode.MonteCarlo)
            {
                candidate = CreateRandomCandidate(
                    leftSpanLengthM,
                    rightSpanLengthM,
                    udlKnPerM);
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
                candidate = CreateRandomCandidate(
                    leftSpanLengthM,
                    rightSpanLengthM,
                    udlKnPerM);
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
                    $"fitness = {fitness,10:F6} | " +
                    $"sym = {result.SymmetryScore,8:F4} | " +
                    $"A = {result.MomentA,8:F1} | " +
                    $"Bps = {result.MomentBPs,8:F1} | " +
                    $"Btot = {result.MomentBTotal,8:F1} | " +
                    $"C = {result.MomentC,8:F1} | " +
                    $"ecc = [{candidate.TendonEccLeftM:F3}, " +
                    $"{candidate.TendonEccLeftSpanMidM:F3}, " +
                    $"{candidate.TendonEccMidSupportM:F3}, " +
                    $"{candidate.TendonEccRightSpanMidM:F3}, " +
                    $"{candidate.TendonEccRightM:F3}]");
            }
            else
            {
                iterationsWithoutImprovement++;
            }

            if (iterationsWithoutImprovement >= patience)
            {
                Console.WriteLine();
                Console.WriteLine($"Stopped after {i} iterations - no improvement for {patience} iterations.");
                break;
            }
        }

        return bestCandidate
            ?? throw new Exception("Optimization failed.");
    }

    private BridgeCandidate CreateZeroCandidate(
        float leftSpanLengthM,
        float rightSpanLengthM,
        float udlKnPerM)
    {
        return new BridgeCandidate
        {
            LeftSpanLengthM = leftSpanLengthM,
            RightSpanLengthM = rightSpanLengthM,
            UdlKnPerM = udlKnPerM,

            TendonEccLeftM = 0.0f,
            TendonEccLeftSpanMidM = 0.0f,
            TendonEccMidSupportM = 0.0f,
            TendonEccRightSpanMidM = 0.0f,
            TendonEccRightM = 0.0f
        };
    }

    private BridgeCandidate CreateRandomCandidate(
        float leftSpanLengthM,
        float rightSpanLengthM,
        float udlKnPerM)
    {
        return new BridgeCandidate
        {
            LeftSpanLengthM = leftSpanLengthM,
            RightSpanLengthM = rightSpanLengthM,
            UdlKnPerM = udlKnPerM,

            TendonEccLeftM = RandomEcc(),
            TendonEccLeftSpanMidM = RandomEcc(),
            TendonEccMidSupportM = RandomEcc(),
            TendonEccRightSpanMidM = RandomEcc(),
            TendonEccRightM = RandomEcc()
        };
    }

    private BridgeCandidate Mutate(BridgeCandidate parent)
    {
        return new BridgeCandidate
        {
            LeftSpanLengthM = parent.LeftSpanLengthM,
            RightSpanLengthM = parent.RightSpanLengthM,
            UdlKnPerM = parent.UdlKnPerM,

            TendonEccLeftM = MutateEcc(parent.TendonEccLeftM),
            TendonEccLeftSpanMidM = MutateEcc(parent.TendonEccLeftSpanMidM),
            TendonEccMidSupportM = MutateEcc(parent.TendonEccMidSupportM),
            TendonEccRightSpanMidM = MutateEcc(parent.TendonEccRightSpanMidM),
            TendonEccRightM = MutateEcc(parent.TendonEccRightM)
        };
    }

    private float MutateEcc(float value)
    {
        var delta =
            ((float)_random.NextDouble() * 2.0f - 1.0f) * MutationMaxDelta;

        var mutated = Math.Clamp(value + delta, EccMin, EccMax);

        if (Math.Abs(mutated) < SnapToZeroTolerance)
            return 0.0f;

        return mutated;
    }

    private float RandomEcc()
    {
        return EccMin + (float)_random.NextDouble() * (EccMax - EccMin);
    }
}