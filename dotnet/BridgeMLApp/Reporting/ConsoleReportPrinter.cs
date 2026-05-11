using BridgeMLApp.Domain;
using BridgeMLApp.ML;

namespace BridgeMLApp.Reporting;

public static class ConsoleReportPrinter
{
    public static void PrintExperimentInfo(MlExperiment experiment)
    {
        Console.WriteLine("CSV loaded successfully.");
        Console.WriteLine($"Experiment: {experiment.Name}");
        Console.WriteLine($"Target: {experiment.TargetColumn}");
        Console.WriteLine("Features:");

        foreach (var feature in experiment.FeatureColumns)
            Console.WriteLine($"- {feature}");

        Console.WriteLine();
    }

    public static void PrintLabelStats(IReadOnlyList<BeamRecord> rows)
    {
        var minLabel = rows.Min(r => r.Label);
        var maxLabel = rows.Max(r => r.Label);
        var avgLabel = rows.Average(r => r.Label);

        Console.WriteLine("=== LABEL STATS ===");
        Console.WriteLine($"Min: {minLabel:F3}");
        Console.WriteLine($"Max: {maxLabel:F3}");
        Console.WriteLine($"Avg: {avgLabel:F3}");
        Console.WriteLine($"Range: {(maxLabel - minLabel):F3}");
        Console.WriteLine();
    }

    public static void PrintRandomSamples(
        IReadOnlyList<BeamRecord> rows,
        MlExperiment experiment,
        int count = 5)
    {
        var rng = new Random();

        Console.WriteLine("=== RANDOM SAMPLES ===");

        foreach (var row in rows.OrderBy(_ => rng.Next()).Take(count))
        {
            var featureStrings = row.Features
                .Select((value, index) =>
                    $"{experiment.FeatureColumns[index]}={value:F3}");

            Console.WriteLine(
                $"Features: {string.Join(", ", featureStrings)} | " +
                $"Label={row.Label:F3}");
        }

        Console.WriteLine();
    }

    public static void PrintRanking(IReadOnlyList<RegressionResult> results)
    {
        Console.WriteLine();
        Console.WriteLine("=== SUMMARY RESULTS (5-FOLD CROSS-VALIDATION) ===");

        for (int i = 0; i < results.Count; i++)
        {
            var r = results[i];

            Console.WriteLine(
                $"{i + 1}. {r.ModelName,-22} | " +
                $"R² = {r.AvgRSquared:F4} ± {r.StdRSquared:F4} | " +
                $"MAE = {r.AvgMeanAbsoluteError:F6} ± {r.StdMeanAbsoluteError:F6} | " +
                $"RMSE = {r.AvgRootMeanSquaredError:F6} ± {r.StdRootMeanSquaredError:F6}");
        }
    }
}