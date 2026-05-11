using BridgeEAApp.Optimization;
using BridgeEAApp.Surrogate;

namespace BridgeEAApp.Reporting;

internal static class ConsoleResultPrinter
{
    public static void PrintBestCandidate(
        BridgeCandidate best,
        BridgeFitnessResult bestResult)
    {
        Console.WriteLine();
        Console.WriteLine("=== BEST CANDIDATE ===");
        Console.WriteLine($"Fitness:              {bestResult.Fitness:F6}");
        Console.WriteLine($"Hyperstatic score:       {bestResult.HyperstaticEffectScore:F6}");
        Console.WriteLine($"Middle support score:    {bestResult.MiddleSupportMomentScore:F6}");
        Console.WriteLine($"Deflection score:        {bestResult.DeflectionScore:F6}");
        Console.WriteLine($"Span moment score:       {bestResult.SpanMomentScore:F6}");

        Console.WriteLine();
        Console.WriteLine("=== SUPPORTS ===");
        Console.WriteLine($"Moment A total:       {bestResult.MomentA:F3}");
        Console.WriteLine($"Moment B ps:          {bestResult.MomentBPs:F3}");
        Console.WriteLine($"Moment B total:       {bestResult.MomentBTotal:F3}");
        Console.WriteLine($"Moment C total:       {bestResult.MomentC:F3}");

        Console.WriteLine();
        Console.WriteLine("=== DEFLECTIONS ===");
        Console.WriteLine($"Left dz min:          {bestResult.LeftDeflectionMin:F6}");
        Console.WriteLine($"Left dz max:          {bestResult.LeftDeflectionMax:F6}");
        Console.WriteLine($"Right dz min:         {bestResult.RightDeflectionMin:F6}");
        Console.WriteLine($"Right dz max:         {bestResult.RightDeflectionMax:F6}");

        Console.WriteLine();
        Console.WriteLine("=== SPAN MOMENTS ===");
        Console.WriteLine($"Left moment min:      {bestResult.LeftMomentMin:F3}");
        Console.WriteLine($"Left moment max:      {bestResult.LeftMomentMax:F3}");
        Console.WriteLine($"Right moment min:     {bestResult.RightMomentMin:F3}");
        Console.WriteLine($"Right moment max:     {bestResult.RightMomentMax:F3}");

        Console.WriteLine();
        Console.WriteLine("=== ECCENTRICITIES ===");
        Console.WriteLine($"EccLeft:              {best.TendonEccLeftM:F3}");
        Console.WriteLine($"EccLeftMid:           {best.TendonEccLeftSpanMidM:F3}");
        Console.WriteLine($"EccSupport:           {best.TendonEccMidSupportM:F3}");
        Console.WriteLine($"EccRightMid:          {best.TendonEccRightSpanMidM:F3}");
        Console.WriteLine($"EccRight:             {best.TendonEccRightM:F3}");

        Console.WriteLine();
        Console.WriteLine("=== SYMMETRY ===");
        Console.WriteLine($"Symmetry penalty:     {bestResult.SymmetryPenaltyApplied}");
        Console.WriteLine($"Symmetry score:       {bestResult.SymmetryScore:F6}");
    }
}